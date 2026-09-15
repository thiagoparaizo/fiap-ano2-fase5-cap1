# Relatório – Parte 2: Interface de Interação com o Usuário

**Projeto:** CardioIA – Fase 5, Capítulo 1
**Aluno:** Thiago Paraizo da Silva – RM566159 | 2TIAOA-2026

---

## 1. Tecnologias

Interface web *single-page* construída com **HTML5, CSS3 e JavaScript puro (Vanilla JS)**,
servida diretamente pelo backend Flask da Parte 1 — o que elimina qualquer etapa de build
e mantém o projeto executável com um único comando.

| Arquivo | Responsabilidade |
|---|---|
| [`templates/index.html`](templates/index.html) | Estrutura da página (renderizada pelo Flask via `render_template`) |
| [`static/style.css`](static/style.css) | Estilos, paleta de cores e animações |
| [`static/chat.js`](static/chat.js) | Sessão, comunicação com a API e atualização da interface |

A escolha por JS puro foi deliberada: o volume de lógica do chat (uma sessão, duas chamadas
REST e a renderização de bolhas) não justifica o peso de um framework, e a ausência de
dependências de frontend torna a demonstração reproduzível sem `npm install`.

### 1.1 Paleta de cores

| Cor | Uso |
|---|---|
| `#0d1b2a` azul-marinho escuro | Cabeçalho |
| `#457b9d` azul médio | Bolhas do assistente |
| `#2d6a4f` verde acinzentado | Bolhas do usuário |
| `#e63946` vermelho | Emergência e botão de envio |
| `#52b788` verde | Indicador de status conectado |

---

## 2. Funcionalidades da Interface

- **Inicialização automática de sessão** — ao carregar a página, o `chat.js` chama
  `POST /api/session` e exibe a mensagem de boas-vindas do CardioIA.
- **Envio por clique ou tecla Enter** — o campo de texto está dentro de um `<form>`, então
  o envio por Enter é comportamento nativo do navegador, sem listener de teclado.
- **Bolhas de mensagem diferenciadas** — usuário à direita (verde) e assistente à esquerda
  (azul), com cantos assimétricos e animação de entrada.
- **Banner de emergência piscante** — quando a resposta traz `is_emergency: true`, um banner
  vermelho com o telefone do SAMU aparece no topo por 10 segundos e a bolha da resposta
  também fica vermelha e em negrito.
- **Indicador de "digitando..."** — três pontos animados enquanto a requisição está em curso,
  dando retorno imediato ao usuário.
- **Sugestões rápidas** — quatro botões de atalho (frequência cardíaca, pressão arterial,
  relatar sintoma, ajuda) que enviam a mensagem correspondente, facilitando a descoberta das
  funcionalidades sem exigir que o usuário adivinhe o que perguntar.
- **Indicador de status** — o ponto no cabeçalho fica verde quando conectado e vermelho
  quando o backend não responde; o *tooltip* informa se o assistente ativo é o Watson ou o
  mock local.
- **Aviso legal permanente** — a nota "não substitui consulta médica" fica fixa acima do
  campo de entrada, visível durante toda a conversa.
- **Encerramento de sessão** — ao fechar a aba, `navigator.sendBeacon` chama
  `/api/delete-session`, liberando a sessão no Watson.
- **Layout responsivo** — em telas abaixo de 520 px o chat ocupa a tela inteira, sem bordas
  arredondadas, comportando-se como um aplicativo de mensagens.

### 2.1 Tratamento de erros

A interface nunca trava em silêncio. Falha de rede, backend fora do ar ou erro retornado
pela API são exibidos como uma mensagem do assistente com o ícone ⚠️, orientando o usuário
a verificar se o backend está rodando.

### 2.2 Segurança do conteúdo renderizado

O texto de cada mensagem é escapado antes de ir para o DOM (`escapeHtml`), e só depois as
quebras de linha são convertidas em `<br>`. Assim as respostas do Watson preservam a
formatação em várias linhas sem abrir espaço para injeção de HTML a partir do que o usuário
digita.

---

## 3. Fluxo de Interação

```
Usuário digita
      │
      ▼
chat.js  ──POST /api/message──►  Flask (app.py)
                                      │
                                      ├─ modo watson → IBM Watson Assistant (NLP)
                                      └─ modo mock   → mock_assistant.py (fallback)
                                      │
      ◄──{response, intent, is_emergency}──┘
      │
      ├─ renderiza a bolha do assistente
      └─ se is_emergency → banner vermelho + bolha em destaque
```

---

## 4. Evidências

| Evidência | Arquivo |
|---|---|
| Interface do chat em uso | `../docs/screenshots/chat-interface.png` |
| Banner de emergência acionado | `../docs/screenshots/chat-alerta.png` |
| Consulta de sintomas | `../docs/screenshots/chat-alerta.png` |
| Intents no Watson Assistant | `../docs/screenshots/watson-intents.png` |
| Dialog tree no Watson Assistant | `../docs/screenshots/watson-dialog-flow.png` |


---

## 5. Repositório

https://github.com/thiagoparaizo/fiap-ano2-fase5-cap1.git
