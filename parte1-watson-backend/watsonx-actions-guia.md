# Guia — Importando e melhorando as Actions no watsonx Assistant

**Projeto:** CardioIA – Fase 5, Capítulo 1

---

## ⚠️ Leia antes de importar: o que o CSV faz (e o que não faz)

A documentação que você colou descreve **dois formatos diferentes** de importação, e
vale a pena deixar isso muito claro antes de você importar qualquer coisa:

| Formato | O que importa | O que **não** importa |
|---|---|---|
| **JSON** (Global settings → Upload/Download) | Actions completas: steps, condições, variáveis, ramificações — é o *backup/restore* de tudo que existe na instância | — |
| **CSV** (ícone de Upload na página de Actions — "Uploading intents as actions") | Cria **1 action por intent**, com as frases apenas como *exemplos de acionamento* | **Steps, condições, perguntas de acompanhamento, entidades/variáveis** — nada disso vem no CSV |

Ou seja: o CSV é um **ponto de partida rápido** (bootstrap), não uma forma de trazer o
fluxo de diálogo completo que já modelamos em [`watson_skill.json`](watson_skill.json)
para a plataforma clássica. Se a sua queixa é "está simples, muita coisa não funciona
bem", **o CSV sozinho não resolve isso** — ele só cria o esqueleto (nome da action +
frases de exemplo). A lógica de "isso funciona melhor" (priorizar emergência, perguntar
detalhes do sintoma, etc.) precisa ser adicionada manualmente nos *steps* de cada action,
na tela do watsonx Assistant — é a seção 2 deste guia.

**Arquivo gerado:** [`watsonx_actions_import.csv`](watsonx_actions_import.csv)
— 87 frases distribuídas em 10 actions, sem vírgulas dentro das frases (evita ambiguidade
em parsers de CSV mais simples), sem BOM, codificado em UTF-8.

| Action (a partir do intent) | Nº de frases |
|---|---|
| `saudacao` | 10 |
| `despedida` | 8 |
| `relatar sintoma` | 12 |
| `perguntar pressao` | 9 |
| `perguntar frequencia` | 9 |
| `perguntar medicamento` | 8 |
| `marcar consulta` | 7 |
| `emergencia` | 9 |
| `ajuda` | 7 |
| `informacao geral` | 8 |

> O fallback `nao_entendeu` **não** está no CSV — no watsonx Assistant Actions isso não é
> uma action, é o comportamento padrão de "não entendi" do próprio assistente
> (configurável em *Global settings → Options*).

### Como importar

1. Vá em **Actions** → ícone de **Upload** (⬆, não é o de "Global settings").
2. Selecione `watsonx_actions_import.csv`.
3. O sistema valida, cria 10 novas actions (uma por intent) e treina automaticamente.
4. Se alguma action com o mesmo nome já existir na sua instância, as frases novas serão
   somadas como exemplos adicionais — revise para não duplicar o que você já tinha
   criado manualmente.

---

## 2. O que fazer depois de importar (a parte que realmente melhora o assistente)

O CSV te dá 10 actions treináveis com bons exemplos de frase. Para chegar perto da
lógica do plano original (12 nós de diálogo, com emergência sempre prioritária e
perguntas de acompanhamento por sintoma), edite cada action na UI seguindo o roteiro
abaixo. Isso é trabalho manual — não há um formato de arquivo público e estável para
importar *steps* completos na nova experiência de Actions.

### 2.1 Prioridade da emergência (o ajuste mais importante)

Na action **emergencia**:

- Abra a action → aba **"Customer wants to..."** → adicione mais variações, incluindo
  frases curtas e urgentes que usuários reais digitam com erro de digitação: "infarto",
  "socorro", "n consigo respirar", "192", "chamem alguem".
- Em **Steps**, deixe **apenas um step**, sem perguntas de acompanhamento, com a
  resposta direta (telefones do SAMU/Bombeiros). Emergência não deve ter um fluxo longo.
- Em **Global settings → Actions → escopo de digressão**: desligue
  ("Disable digressing into other actions") a possibilidade de o usuário ser desviado
  para outra action no meio da emergência, e marque a action de emergência para
  **não permitir interrupção por outras** (na aba de configurações da própria action,
  seção "Customer can interrupt this action" → desmarcar).
- Teste digitando frases ambíguas que misturam sintoma comum + urgência
  ("estou com muita dor no peito agora") para confirmar que cai em `emergencia`, não em
  `relatar sintoma`.

### 2.2 Relatar sintoma — transformar em pergunta de acompanhamento (slot filling)

Hoje provavelmente essa action só devolve uma resposta genérica. Para ficar como o
nó 4 do plano (dor no peito / palpitação / falta de ar / default):

1. Adicione um **step do tipo "Ask a question"** logo no início, com uma pergunta de
   múltipla escolha: *"Qual desses sintomas você está sentindo?"* com opções
   **Dor no peito**, **Palpitação**, **Falta de ar / tontura / fadiga**, **Outro**.
2. Salve a resposta em uma **variável de sessão** (ex.: `sintoma_relatado`).
3. Adicione **steps condicionais** logo depois, cada um com a condição
   `sintoma_relatado is Dor no peito` (e assim por diante), cada um com a resposta
   específica daquele sintoma (as mesmas mensagens que já estão em
   [`watson_skill.json`](watson_skill.json), nós 4.1–4.3).
4. Deixe um último step **sem condição** (fallback dentro da action) com a orientação
   genérica — equivalente ao nó 4.4 (`default`).

O mesmo padrão (pergunta → variável → steps condicionais) resolve **pressão arterial**
(alta/baixa/valores de referência) replicando o nó 5.

### 2.3 Ajustes que costumam causar "muita coisa não funciona bem"

| Sintoma do problema | Causa provável | Ajuste |
|---|---|---|
| Frase clara de emergência cai em `relatar sintoma` | Poucos exemplos de emergência, ou frases parecidas demais entre as duas actions | Aumente os exemplos de `emergencia` com variações de urgência; revise disambiguation em *Global settings* |
| Assistente pergunta de novo algo que o usuário já respondeu na mesma frase | Falta pré-preencher a variável a partir da própria mensagem inicial | Nos steps de "Ask a question", habilite **"Also look for the answer in the customer's initial message"** |
| Duas actions "brigam" pela mesma frase | Exemplos muito parecidos entre `perguntar_pressao` e `perguntar_frequencia`, por exemplo | Rode o **Analytics → Actions** para ver colisões reais e ajuste os exemplos |
| Resposta genérica demais | Action com um único step de texto fixo | Aplique o padrão de slot filling da seção 2.2 |

### 2.4 Ordem de avaliação

Na experiência de Actions não existe mais "irmão anterior" (`previous_sibling`) como no
dialog clássico — a ordenação de prioridade é feita por:
- **Especificidade dos exemplos** (o motor de NLU escolhe a de maior confiança);
- **Condições explícitas** (uma action pode exigir uma variável de contexto já definida
  para dar mais precisão);
- **Configuração de digressão**, que você usa para impedir que a emergência seja
  "atropelada" por outra action.

---

## 3. Referência: lógica original completa

Todo o desenho de conversa (12 nós, 3 entidades, ordem de prioridade) continua
documentado em [`watson_skill.json`](watson_skill.json) e no
[Relatório da Parte 1](relatorio-parte1.md) — use-o como roteiro de conteúdo (textos das
respostas, ordem de prioridade) ao recriar os steps na interface de Actions, mesmo que o
arquivo em si não seja diretamente importável nessa experiência mais nova do produto.
