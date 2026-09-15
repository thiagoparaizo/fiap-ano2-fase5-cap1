# Relatório – IR Além 2: RPA + Dados Híbridos

**Projeto:** CardioIA – Fase 5, Capítulo 1
**Aluno:** Thiago Paraizo da Silva – RM566159 | 2TIAOA-2026

---

## 1. Objetivo

Simular um robô de automação (RPA) que monitora leituras clínicas de pacientes
cadastrados, detecta anomalias com **Isolation Forest** e registra os alertas em dois
bancos de natureza diferente — um **relacional** (SQLite) e um **não relacional**
(MongoDB) — demonstrando um cenário híbrido de persistência de dados.

---

## 2. Arquitetura da solução

```
                         ┌─────────────────────┐
                         │  rpa_monitor.py      │
                         │  (robô de 3 ciclos)  │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                      ▼
     ┌──────────────────┐  ┌────────────────┐   ┌───────────────────────┐
     │ SQLite            │  │ Isolation      │   │ MongoDB (Docker)      │
     │ cardio_rpa.db      │  │ Forest         │   │ cardio_logs           │
     │                    │  │ (scikit-learn) │   │                       │
     │ pacientes          │  │                │   │ alertas               │
     │ leituras_clinicas ─┼─►│ detecta        │──►│  (log completo +      │
     │ alertas ◄──────────┼──┤ anomalias      │   │   score do modelo)    │
     │  (estrutura fixa)  │  │                │   │ execucoes_rpa         │
     └────────────────────┘  └────────────────┘   │  (dado semiestrut.)   │
                                                    └───────────────────────┘
```

- **SQLite** guarda os dados estruturados e normalizados: pacientes, leituras e o
  alerta resumido (nível + descrição) — consultável com SQL puro.
- **MongoDB** guarda o **log completo** da detecção: métricas em subdocumento,
  score contínuo do modelo e timestamp — dado semiestruturado que não precisa de
  schema fixo e cresce naturalmente a cada execução.

---

## 3. Banco relacional (SQLite) — `db_schema.sql`

Três tabelas com chave estrangeira:

| Tabela | Papel |
|---|---|
| `pacientes` | Cadastro dos pacientes monitorados (seed: João Silva, Maria Santos, Carlos Oliveira) |
| `leituras_clinicas` | Série temporal de leituras: pressão, frequência cardíaca, temperatura, adesão ao medicamento |
| `alertas` | Alertas gerados pelo RPA, com nível (`baixo`/`medio`/`alto`/`critico`) e descrição |

---

## 4. Banco não relacional (MongoDB) — Docker

Subido via [`docker-compose.yml`](docker-compose.yml):

```bash
cd ir-alem-2-rpa-dados
docker compose up -d
```

> **Nota técnica:** o plano original previa a imagem `mongo:7-alpine`, mas essa tag
> **não existe** no Docker Hub — a imagem oficial do Mongo não publica variante Alpine.
> Foi usada a tag oficial **`mongo:7`**, testada e funcional.
>
> A porta do host foi mapeada para **27018** (em vez de 27017) para não conflitar com
> outro MongoDB que já podia estar rodando na máquina de desenvolvimento na porta
> padrão. `rpa_monitor.py` já aponta para `mongodb://localhost:27018/`.

Duas coleções são escritas pelo robô:

| Coleção | Conteúdo |
|---|---|
| `alertas` | Um documento por anomalia: paciente, métricas (subdocumento), nível, descrição e `score_anomalia` do Isolation Forest |
| `execucoes_rpa` | Um documento por ciclo do robô: quantas leituras foram analisadas e quantas anomalias foram encontradas |

---

## 5. Detecção de anomalias (Isolation Forest)

O modelo `sklearn.ensemble.IsolationForest` (contaminação = 10%) é treinado a cada
ciclo sobre as 4 variáveis clínicas (`pressao_sistolica`, `pressao_diastolica`,
`frequencia_cardiaca`, `temperatura`) das últimas 200 leituras. Leituras marcadas como
anômalas (`-1`) recebem, em seguida, uma **classificação de nível de alerta por regras
clínicas simples** (ex.: PAS ≥ 180 mmHg → `critico`; FC > 120 bpm → escalona o nível;
febre ou não adesão ao medicamento → eleva para pelo menos `medio`).

Essa combinação — detecção estatística (não supervisionada) + regras de domínio — evita
que o alerta dependa só do modelo, mas também não descarta anomalias que as regras fixas
não previam.

---

## 6. Resiliência do RPA

Se o MongoDB não estiver disponível (container não subido, rede instável), o robô
**não interrompe a execução**: registra um aviso no console, grava normalmente os
alertas no SQLite e apenas deixa de persistir o log estendido no Mongo. Esse
comportamento foi testado explicitamente (parando o container e rodando um ciclo).

---

## 7. Execução e evidências de teste

```bash
cd ir-alem-2-rpa-dados
docker compose up -d          # sobe o MongoDB na porta 27018
pip install pandas numpy scikit-learn pymongo
python rpa_monitor.py          # roda o seed + 3 ciclos de 10s
```

Testes realizados durante o desenvolvimento (ambiente Windows, Docker Desktop):

| Teste | Resultado |
|---|---|
| Seed do SQLite (3 pacientes, tabelas criadas) | ✅ OK |
| Geração de 100 leituras simuladas | ✅ OK — ~10% marcadas como anômalas pelo gerador |
| Isolation Forest sobre as leituras | ✅ 10 anomalias detectadas em 100 leituras |
| Gravação simultânea SQLite + MongoDB | ✅ 10 alertas em `alertas` (SQLite) e `alertas`/`execucoes_rpa` (MongoDB) |
| Acentuação/UTF-8 nos textos (`João`, `crítica`, `°C`) | ✅ Preservada nos dois bancos |
| Execução com MongoDB indisponível | ✅ RPA continua, grava só no SQLite, sem exceção não tratada |

---

## 8. Estrutura de arquivos

```
ir-alem-2-rpa-dados/
├── docker-compose.yml        ← Sobe o MongoDB (porta 27018 no host)
├── db_schema.sql              ← Schema SQLite (pacientes, leituras, alertas)
├── rpa_monitor.py              ← Robô: seed, simulação, Isolation Forest, persistência
└── relatorio-ir-alem-2.md     ← Este relatório
```

`cardio_rpa.db` (SQLite) é gerado localmente na primeira execução e está no
`.gitignore` do repositório — não é versionado.
