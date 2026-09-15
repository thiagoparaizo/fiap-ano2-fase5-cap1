"""
CardioIA – IR ALÉM 2
RPA Monitor: lê dados clínicos (SQLite), detecta anomalias (Isolation Forest),
registra logs e alertas (MongoDB).

Fluxo de cada ciclo:
    1. Carrega as leituras clínicas mais recentes do SQLite.
    2. Aplica um Isolation Forest para sinalizar leituras estatisticamente
       anômalas (combinação incomum de pressão, frequência e temperatura).
    3. Classifica cada anomalia por regras clínicas simples (nível de alerta).
    4. Grava o alerta estruturado no SQLite e o log completo da detecção
       (métricas + score do modelo) no MongoDB.

Execução:
    python rpa_monitor.py
"""

import random
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from sklearn.ensemble import IsolationForest

# ── Caminhos e conexões ──────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cardio_rpa.db"
SCHEMA_PATH = BASE_DIR / "db_schema.sql"

MONGO_URI = "mongodb://localhost:27018/"
MONGO_DB = "cardio_logs"

NIVEIS = ["baixo", "medio", "alto", "critico"]


def get_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_mongo():
    """Retorna o database do MongoDB, ou None se o servidor estiver indisponível."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        return client[MONGO_DB]
    except PyMongoError as erro:
        print(f"[AVISO] MongoDB indisponível ({erro}). "
              f"Suba o container com 'docker compose up -d' antes de rodar o RPA "
              f"para persistir os logs. Os alertas ainda serão gravados no SQLite.")
        return None


# ── Seed inicial: cria tabelas e pacientes de exemplo ────────
def setup_database():
    conn = get_sqlite()
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    cur = conn.cursor()
    if cur.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO pacientes (nome, idade) VALUES (?, ?)",
            [("João Silva", 62), ("Maria Santos", 48), ("Carlos Oliveira", 71)],
        )
        conn.commit()
    conn.close()
    print("[SETUP] Banco SQLite inicializado.")


# ── Gerador de leituras simuladas ─────────────────────────────
def simular_leituras(n=50):
    """Gera n leituras simuladas com ~10% de anomalias intencionais."""
    conn = get_sqlite()
    cur = conn.cursor()
    ids = [row[0] for row in cur.execute("SELECT id FROM pacientes").fetchall()]

    leituras = []
    for _ in range(n):
        pid = random.choice(ids)
        anomalia = random.random() < 0.10

        if anomalia:
            ps = random.randint(160, 200)     # hipertensão severa
            pd_ = random.randint(100, 120)
            fc = random.randint(120, 160)     # taquicardia
            temp = round(random.uniform(38.5, 40.0), 1)  # febre
            adesao = 0
        else:
            ps = random.randint(110, 139)
            pd_ = random.randint(70, 89)
            fc = random.randint(60, 100)
            temp = round(random.uniform(36.0, 37.4), 1)
            adesao = 1

        leituras.append((pid, ps, pd_, fc, temp, adesao))

    cur.executemany(
        """INSERT INTO leituras_clinicas
           (paciente_id, pressao_sistolica, pressao_diastolica,
            frequencia_cardiaca, temperatura, adesao_medicamento)
           VALUES (?,?,?,?,?,?)""",
        leituras,
    )
    conn.commit()
    conn.close()
    print(f"[SIM] {n} leituras simuladas inseridas.")


# ── Lê leituras recentes para análise ─────────────────────────
def carregar_leituras():
    conn = get_sqlite()
    df = pd.read_sql_query(
        """SELECT l.*, p.nome FROM leituras_clinicas l
           JOIN pacientes p ON l.paciente_id = p.id
           ORDER BY l.registrado_em DESC LIMIT 200""",
        conn,
    )
    conn.close()
    return df


# ── Detecção de anomalias com Isolation Forest ────────────────
def detectar_anomalias(df):
    features = ["pressao_sistolica", "pressao_diastolica",
                "frequencia_cardiaca", "temperatura"]
    X = df[features].fillna(df[features].mean())

    iso = IsolationForest(contamination=0.1, random_state=42)
    df = df.copy()
    df["anomalia"] = iso.fit_predict(X)          # -1 = anomalia, 1 = normal
    df["score_anomalia"] = iso.score_samples(X)

    anomalos = df[df["anomalia"] == -1]
    print(f"[ISO] {len(anomalos)} anomalias detectadas em {len(df)} leituras.")
    return anomalos


# ── Classifica o nível de alerta por regras clínicas ──────────
def _escalar(nivel_atual: str, nivel_minimo: str) -> str:
    """Eleva nivel_atual para nivel_minimo se este for mais grave."""
    return max(nivel_atual, nivel_minimo, key=NIVEIS.index)


def classificar_alerta(row):
    nivel = "baixo"
    descricoes = []

    if row["pressao_sistolica"] >= 180:
        nivel = "critico"
        descricoes.append(f"PAS crítica: {row['pressao_sistolica']} mmHg")
    elif row["pressao_sistolica"] >= 160:
        nivel = _escalar(nivel, "alto")
        descricoes.append(f"PAS elevada: {row['pressao_sistolica']} mmHg")

    if row["frequencia_cardiaca"] > 120:
        nivel = "critico" if nivel in ("alto", "critico") else _escalar(nivel, "alto")
        descricoes.append(f"Taquicardia: {row['frequencia_cardiaca']} bpm")

    if row["temperatura"] > 38.5:
        descricoes.append(f"Febre: {row['temperatura']} °C")
        nivel = _escalar(nivel, "medio")

    if not row["adesao_medicamento"]:
        descricoes.append("Não aderiu ao medicamento")
        nivel = _escalar(nivel, "medio")

    descricao = " | ".join(descricoes) if descricoes else "Anomalia detectada pelo modelo"
    return nivel, descricao


# ── Registra alertas no SQLite e logs no MongoDB ──────────────
def registrar_alertas(anomalos, total_leituras, mongo):
    conn = get_sqlite()
    alertas_col = mongo["alertas"] if mongo is not None else None
    execucoes_col = mongo["execucoes_rpa"] if mongo is not None else None

    total_alertas = 0
    for _, row in anomalos.iterrows():
        nivel, descricao = classificar_alerta(row)

        # SQLite: alerta estruturado (dado relacional)
        conn.execute(
            """INSERT INTO alertas (paciente_id, tipo, descricao, nivel)
               VALUES (?, ?, ?, ?)""",
            (int(row["paciente_id"]), "anomalia_isolationforest", descricao, nivel),
        )

        # MongoDB: log completo da detecção (dado semiestruturado)
        if alertas_col is not None:
            alertas_col.insert_one({
                "paciente_id": int(row["paciente_id"]),
                "paciente_nome": row["nome"],
                "leitura_id": int(row["id"]),
                "metricas": {
                    "pressao": f"{row['pressao_sistolica']}/{row['pressao_diastolica']}",
                    "fc_bpm": int(row["frequencia_cardiaca"]),
                    "temperatura": float(row["temperatura"]),
                    "adesao": bool(row["adesao_medicamento"]),
                },
                "nivel": nivel,
                "descricao": descricao,
                "score_anomalia": float(row["score_anomalia"]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        total_alertas += 1

    conn.commit()
    conn.close()

    if execucoes_col is not None:
        execucoes_col.insert_one({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "leituras_analisadas": total_leituras,
            "anomalias_detectadas": total_alertas,
            "status": "concluido",
        })

    destino = "SQLite + MongoDB" if mongo is not None else "SQLite (MongoDB indisponível)"
    print(f"[RPA] {total_alertas} alertas registrados ({destino}).")
    return total_alertas


# ── Loop principal do robô ─────────────────────────────────────
def executar_ciclo_rpa():
    print("=" * 55)
    print("  CardioIA RPA Monitor — Iniciando ciclo")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    df = carregar_leituras()
    if df.empty:
        print("[RPA] Nenhuma leitura encontrada. Gerando dados simulados...")
        simular_leituras(50)
        df = carregar_leituras()

    mongo = get_mongo()
    anomalos = detectar_anomalias(df)
    total = registrar_alertas(anomalos, len(df), mongo)
    print(f"[RPA] Ciclo concluído. {total} alertas gerados.")


# ── Execução ────────────────────────────────────────────────────
if __name__ == "__main__":
    setup_database()
    simular_leituras(100)   # Seed inicial de dados

    N_CICLOS = 3
    for ciclo in range(1, N_CICLOS + 1):
        print(f"\n>>> CICLO {ciclo} de {N_CICLOS} <<<")
        executar_ciclo_rpa()
        if ciclo < N_CICLOS:
            time.sleep(10)

    print("\n[DONE] Demonstração concluída.")
    print(f"Verifique os alertas em '{DB_PATH.name}' (SQLite) e os logs no MongoDB.")
