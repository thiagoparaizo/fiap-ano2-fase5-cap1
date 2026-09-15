"""
CardioIA - Fase 5, Cap 1
Backend Flask: integração com IBM Watson Assistant.

Endpoints REST:
    GET    /                     → serve a interface de chat (Parte 2)
    POST   /api/session          → cria uma sessão no Watson Assistant
    POST   /api/message          → envia mensagem e devolve a resposta do assistente
    DELETE /api/delete-session   → encerra a sessão
    GET    /health               → verificação de saúde e modo de operação

Modo de operação (variável ASSISTANT_MODE no .env):
    auto   → usa o Watson se houver credenciais; caso contrário, o mock local
    watson → força o Watson
    mock   → força o assistente mock local (fallback da seção 11 do plano)
"""

import os
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

import mock_assistant
from watson_config import ASSISTANT_ID, get_watson_client, watson_credentials_ok

load_dotenv()

# ── Aplicação ────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder="../parte2-interface/templates",
    static_folder="../parte2-interface/static",
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cardio-dev-key")
CORS(app)


# ── Seleção do backend conversacional ────────────────────────

def _resolver_modo() -> str:
    """Decide entre 'watson' e 'mock' conforme ASSISTANT_MODE e as credenciais."""
    modo = os.getenv("ASSISTANT_MODE", "auto").strip().lower()

    if modo == "mock":
        return "mock"
    if modo == "watson":
        return "watson"
    return "watson" if watson_credentials_ok() else "mock"


MODO = _resolver_modo()
watson = None

if MODO == "watson":
    try:
        watson = get_watson_client()
        print(f"[CardioIA] Modo: Watson Assistant (assistant_id={ASSISTANT_ID[:8]}...)")
    except Exception as erro:  # credenciais inválidas → não bloqueia a demonstração
        print(f"[CardioIA] Falha ao inicializar o Watson ({erro}). Usando mock local.")
        MODO = "mock"

if MODO == "mock":
    print("[CardioIA] Modo: assistente MOCK local (fallback — sem chamadas à nuvem).")


# ── Rotas ────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve a interface de chat."""
    return render_template("index.html")


@app.route("/api/session", methods=["POST"])
def create_session():
    """Cria uma nova sessão de conversa por usuário."""
    if MODO == "mock":
        return jsonify({"session_id": mock_assistant.create_session(), "mode": "mock"})

    try:
        resultado = watson.create_session(assistant_id=ASSISTANT_ID).get_result()
        return jsonify({"session_id": resultado["session_id"], "mode": "watson"})
    except Exception as erro:
        return jsonify({"error": f"Erro ao criar sessão Watson: {erro}"}), 500


@app.route("/api/message", methods=["POST"])
def send_message():
    """
    Recebe a mensagem do frontend e devolve a resposta do assistente.

    Payload: { "session_id": "...", "message": "texto do usuário" }
    Retorno: { "response": "...", "intent": "...", "is_emergency": bool }
    """
    dados = request.get_json(silent=True) or {}
    mensagem = dados.get("message", "").strip()
    session_id = dados.get("session_id", "").strip()

    if not mensagem:
        return jsonify({"error": "Mensagem vazia"}), 400
    if not session_id:
        return jsonify({"error": "session_id ausente"}), 400

    if MODO == "mock":
        resposta = mock_assistant.message(mensagem)
        resposta["mode"] = "mock"
        return jsonify(resposta)

    try:
        resultado = watson.message(
            assistant_id=ASSISTANT_ID,
            session_id=session_id,
            input={"message_type": "text", "text": mensagem,
                   "options": {"return_context": True}},
            context={"global": {"system": {"user_id": str(uuid.uuid4())}}},
        ).get_result()

        saida = resultado.get("output", {})

        # Concatena todas as respostas de texto devolvidas pelo dialog node
        textos = []
        for item in saida.get("generic", []):
            if item.get("response_type") == "text" and item.get("text"):
                textos.append(item["text"])

        # Intent de maior confiança — usado para sinalizar emergência no frontend
        intents = saida.get("intents", [])
        intent_principal = intents[0].get("intent") if intents else None

        return jsonify({
            "response": "\n".join(textos) if textos else "Não entendi. Pode repetir?",
            "intent": intent_principal,
            "is_emergency": intent_principal == "emergencia",
            "mode": "watson",
        })

    except Exception as erro:
        return jsonify({"error": f"Erro ao contatar Watson: {erro}"}), 500


@app.route("/api/delete-session", methods=["DELETE", "POST"])
def delete_session():
    """Encerra a sessão de conversa (aceita POST para uso com navigator.sendBeacon)."""
    dados = request.get_json(silent=True, force=True) or {}
    session_id = dados.get("session_id", "").strip()

    if MODO == "mock" or not session_id:
        return jsonify({"status": "ok"})

    try:
        watson.delete_session(assistant_id=ASSISTANT_ID, session_id=session_id)
        return jsonify({"status": "ok"})
    except Exception as erro:
        return jsonify({"error": str(erro)}), 500


@app.route("/health")
def health():
    """Verificação de saúde — informa qual backend conversacional está ativo."""
    return jsonify({
        "status": "ok",
        "service": "CardioIA Chat Backend",
        "mode": MODO,
    })


if __name__ == "__main__":
    porta = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").strip().lower() == "true"
    app.run(host="0.0.0.0", port=porta, debug=debug)
