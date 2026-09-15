/**
 * CardioIA – Fase 5, Cap 1
 * Frontend do chat: gerencia a sessão do assistente, o envio/recebimento
 * de mensagens e a sinalização visual de emergência.
 */

// A página é servida pelo próprio Flask, então a origem já é a do backend.
const API_BASE = window.location.origin;

const EMERGENCY_BANNER_MS = 10000;

let sessionId = null;

// ── Elementos ──────────────────────────────────────────────

const el = {
  messages: document.getElementById("messagesArea"),
  typing: document.getElementById("typingIndicator"),
  banner: document.getElementById("emergencyBanner"),
  status: document.getElementById("statusDot"),
  form: document.getElementById("chatForm"),
  input: document.getElementById("userInput"),
  quick: document.getElementById("quickReplies"),
};

// ── Inicialização da sessão ────────────────────────────────

async function initSession() {
  try {
    const res = await fetch(`${API_BASE}/api/session`, { method: "POST" });
    const data = await res.json();

    if (!res.ok || !data.session_id) {
      throw new Error(data.error || "Resposta inválida do servidor");
    }

    sessionId = data.session_id;
    setStatus(true, data.mode);

    appendMessage(
      "bot",
      "Olá! Sou o CardioIA, seu assistente cardiológico virtual. 🫀\n" +
      "Posso ajudar com informações sobre sintomas, pressão arterial, " +
      "frequência cardíaca e orientações gerais de saúde.\n" +
      "⚠️ Atenção: não substituo consulta médica. Em emergências, ligue 192 (SAMU).\n" +
      "Como posso ajudar hoje?"
    );
  } catch (erro) {
    setStatus(false);
    appendMessage(
      "bot",
      "⚠️ Não foi possível conectar ao servidor. Verifique se o backend está rodando " +
      "(python app.py) e recarregue a página."
    );
  }
}

// ── Envio de mensagem ──────────────────────────────────────

async function sendMessage(texto) {
  const mensagem = (texto ?? el.input.value).trim();
  if (!mensagem || !sessionId) return;

  appendMessage("user", mensagem);
  el.input.value = "";
  showTyping(true);

  try {
    const res = await fetch(`${API_BASE}/api/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: mensagem }),
    });
    const data = await res.json();
    showTyping(false);

    if (data.error) {
      appendMessage("bot", `⚠️ ${data.error}`);
      return;
    }

    appendMessage("bot", data.response, data.is_emergency);

    if (data.is_emergency) {
      showEmergencyBanner();
    }
  } catch (erro) {
    showTyping(false);
    appendMessage("bot", "⚠️ Erro de comunicação com o servidor.");
  }
}

// ── Helpers de interface ───────────────────────────────────

function escapeHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

function appendMessage(role, texto, isEmergency = false) {
  const div = document.createElement("div");
  div.classList.add("message", role);
  if (isEmergency) div.classList.add("emergency");

  // Escapa o conteúdo e preserva as quebras de linha vindas do assistente.
  div.innerHTML = escapeHtml(texto).replace(/\n/g, "<br>");

  el.messages.appendChild(div);
  el.messages.scrollTop = el.messages.scrollHeight;
}

function showTyping(show) {
  el.typing.hidden = !show;
  if (show) el.messages.scrollTop = el.messages.scrollHeight;
}

function showEmergencyBanner() {
  el.banner.hidden = false;
  clearTimeout(showEmergencyBanner.timer);
  showEmergencyBanner.timer = setTimeout(() => {
    el.banner.hidden = true;
  }, EMERGENCY_BANNER_MS);
}

function setStatus(connected, mode) {
  el.status.style.background = connected ? "#52b788" : "#e63946";

  if (!connected) {
    el.status.title = "Desconectado";
    return;
  }
  el.status.title =
    mode === "mock" ? "Conectado (assistente mock local)" : "Conectado (Watson Assistant)";
}

// ── Eventos ────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  initSession();

  el.form.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage();
  });

  el.quick.addEventListener("click", (e) => {
    const botao = e.target.closest("button[data-msg]");
    if (botao) sendMessage(botao.dataset.msg);
  });
});

// Encerra a sessão do assistente ao fechar a aba.
window.addEventListener("beforeunload", () => {
  if (!sessionId) return;
  navigator.sendBeacon(
    `${API_BASE}/api/delete-session`,
    new Blob([JSON.stringify({ session_id: sessionId })], { type: "application/json" })
  );
});
