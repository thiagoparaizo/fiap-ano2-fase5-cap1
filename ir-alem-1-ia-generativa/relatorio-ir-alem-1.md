# Relatório – IR Além 1: Extração de Informações Clínicas com IA Generativa

**Projeto:** CardioIA – Fase 5, Capítulo 1  
**Aluno:** Thiago Paraizo da Silva – RM566159 | 2TIAOA-2026

---

## 1. Objetivo

Usar um modelo de IA Generativa para transformar relatos clínicos em **texto livre**
em uma estrutura JSON padronizada — dados do paciente, sintomas, histórico, sinais
vitais e um nível de urgência sugerido — que poderia alimentar diretamente o backend
do CardioIA (por exemplo, pré-preenchendo o cadastro de uma leitura clínica).

---

## 2. Modelo utilizado

**DeepSeek Chat** (`deepseek-chat`), acessado via SDK `openai` (Python) com a
`base_url` apontando para `https://api.deepseek.com`. A DeepSeek oferece uma API
100% compatível com o padrão OpenAI, o que permite reutilizar o mesmo SDK sem
modificações na lógica de chamada — apenas a `base_url` e o nome do modelo mudam.

Parâmetros de configuração relevantes:

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `model` | `deepseek-chat` | Modelo de propósito geral de alto desempenho |
| `response_format` | `{"type": "json_object"}` | Garante JSON sintaticamente válido na saída, sem necessidade de parsing frágil |
| `temperature` | `0.1` | Reduz variação entre execuções — essencial em contexto clínico |

---

## 3. Estrutura de extração

O prompt instrui o modelo a preencher a estrutura abaixo. Campos não mencionados
explicitamente no relato devem permanecer `null` — o modelo não deve inferir dados
ausentes.

```json
{
  "paciente": { "idade": null, "sexo": null },
  "sintomas_principais": [],
  "historico": {
    "comorbidades": [],
    "medicamentos_em_uso": [],
    "historico_familiar": []
  },
  "sinais_vitais": {
    "pressao_arterial_mmHg": null,
    "frequencia_cardiaca_bpm": null,
    "glicemia_mg_dl": null
  },
  "nivel_urgencia": "baixo|medio|alto|emergencia",
  "recomendacao_triagem": ""
}
```

---

## 4. Resultados obtidos

O notebook foi executado no Google Colab com a chave configurada via Secrets
(`DEEPSEEK_API_KEY`). Os três relatos fictícios abaixo foram processados com sucesso.

---

### Relato 1 — Paciente masculino, 58 anos, dor torácica com irradiação

**Entrada:**
> Paciente de 58 anos, sexo masculino, relata dor no peito há 2 dias, com irradiação para o braço esquerdo. Fumante, hipertenso. Pressão medida hoje: 165/95 mmHg. Frequência cardíaca: 102 bpm.

**Extração:**
```json
{
  "paciente": { "idade": 58, "sexo": "masculino" },
  "sintomas_principais": ["dor no peito", "irradiação para o braço esquerdo"],
  "historico": {
    "comorbidades": ["hipertensão"],
    "medicamentos_em_uso": [],
    "historico_familiar": []
  },
  "sinais_vitais": {
    "pressao_arterial_mmHg": "165/95",
    "frequencia_cardiaca_bpm": 102,
    "glicemia_mg_dl": null
  },
  "nivel_urgencia": "alto",
  "recomendacao_triagem": "Encaminhamento imediato para avaliação cardiológica de emergência devido a dor torácica com irradiação e fatores de risco cardiovascular."
}
```
🟠 **Urgência: ALTO**

---

### Relato 2 — Paciente feminina, 42 anos, palpitações noturnas

**Entrada:**
> Mulher, 42 anos. Queixa de palpitações frequentes, principalmente à noite. Histórico familiar de arritmia. Não usa medicamentos. Sente tontura ocasional. Glicemia em jejum: 98 mg/dL.

**Extração:**
```json
{
  "paciente": { "idade": 42, "sexo": "feminino" },
  "sintomas_principais": ["palpitações frequentes", "tontura ocasional"],
  "historico": {
    "comorbidades": [],
    "medicamentos_em_uso": [],
    "historico_familiar": ["arritmia"]
  },
  "sinais_vitais": {
    "pressao_arterial_mmHg": null,
    "frequencia_cardiaca_bpm": null,
    "glicemia_mg_dl": 98
  },
  "nivel_urgencia": "medio",
  "recomendacao_triagem": "Encaminhar para avaliação cardiológica e realizar eletrocardiograma."
}
```
🟡 **Urgência: MÉDIO**

---

### Relato 3 — Paciente masculino, 70 anos, dispneia e edema

**Entrada:**
> Homem, 70 anos, diabético e sedentário. Relata falta de ar ao subir escadas, piora nas últimas 3 semanas. Edema nos tornozelos. Em uso de Losartana 50mg e Metformina 850mg.

**Extração:**
```json
{
  "paciente": { "idade": 70, "sexo": "masculino" },
  "sintomas_principais": [
    "falta de ar ao subir escadas",
    "piora nas últimas 3 semanas",
    "edema nos tornozelos"
  ],
  "historico": {
    "comorbidades": ["diabetes", "sedentarismo"],
    "medicamentos_em_uso": ["Losartana 50mg", "Metformina 850mg"],
    "historico_familiar": []
  },
  "sinais_vitais": {
    "pressao_arterial_mmHg": null,
    "frequencia_cardiaca_bpm": null,
    "glicemia_mg_dl": null
  },
  "nivel_urgencia": "medio",
  "recomendacao_triagem": "Encaminhar para avaliação médica presencial para investigação de dispneia e edema, com possível insuficiência cardíaca."
}
```
🟡 **Urgência: MÉDIO**

---

## 5. Análise dos resultados

O modelo demonstrou boa capacidade de extração nos três cenários testados:

- **Campos numéricos** (idade, BPM, glicemia, pressão) foram extraídos corretamente nos
  relatos em que aparecem, e mantidos como `null` quando ausentes — conforme instrução
  do prompt.
- **Nível de urgência** foi classificado coerentemente: o Relato 1 recebeu `alto`
  (dor torácica com irradiação e hipertensão descontrolada), enquanto os demais
  receberam `medio` (sintomas crônicos sem sinal imediato de emergência).
- **Recomendações de triagem** foram específicas e clinicamente pertinentes, citando
  encaminhamento de emergência no caso mais grave e eletrocardiograma para investigação
  de arritmia no segundo relato.
- **Medicamentos** foram extraídos com dose e nome corretos no Relato 3
  (`Losartana 50mg`, `Metformina 850mg`), sem inferências indevidas.

---

## 6. Considerações éticas

- **Dados fictícios:** os três relatos usados como entrada são simulados para fins
  didáticos e não correspondem a pacientes reais.
- **LGPD / dado sensível de saúde:** em produção, o relato clínico não deve ser
  enviado a uma API externa sem anonimização prévia e sem base legal adequada para o
  tratamento do dado (consentimento explícito ou outra hipótese da LGPD aplicável a
  dados sensíveis de saúde).
- **Apoio, não substituição:** `nivel_urgencia` e `recomendacao_triagem` são sugestões
  para apoiar a triagem — a decisão clínica final é sempre de um profissional de saúde.
- **Risco de alucinação:** o modelo pode, em relatos ambíguos, inferir um dado não
  informado. O prompt mitiga isso exigindo `null` para dados ausentes, mas qualquer
  uso real exigiria validação humana antes de alimentar um prontuário.

---

## 7. Referências

- DeepSeek. *DeepSeek API Documentation*. https://platform.deepseek.com/docs
- OpenAI. *Python SDK*. https://github.com/openai/openai-python
- Brasil. *Lei Geral de Proteção de Dados Pessoais (LGPD)* — Lei nº 13.709/2018.
