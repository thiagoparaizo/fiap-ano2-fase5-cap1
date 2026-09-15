-- CardioIA – IR Além 2
-- Esquema relacional (SQLite): pacientes monitorados, leituras clínicas e
-- alertas gerados pelo robô de monitoramento (rpa_monitor.py).

-- Tabela de pacientes monitorados
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    idade INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de leituras clínicas
CREATE TABLE IF NOT EXISTS leituras_clinicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    pressao_sistolica INTEGER,
    pressao_diastolica INTEGER,
    frequencia_cardiaca INTEGER,
    temperatura REAL,
    adesao_medicamento BOOLEAN DEFAULT 1,
    registrado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

-- Tabela de alertas gerados pelo RPA
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    descricao TEXT,
    nivel TEXT CHECK(nivel IN ('baixo','medio','alto','critico')),
    resolvido BOOLEAN DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);
