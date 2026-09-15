"""
CardioIA - Fase 5, Cap 1
Configuração e fábrica do cliente IBM Watson Assistant v2.

As credenciais nunca ficam no código: são lidas do arquivo `.env`
(ver `.env.example`), que está no `.gitignore`.
"""

import os

from dotenv import load_dotenv
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2

load_dotenv()

# Versão da API do Watson Assistant v2 utilizada no projeto
WATSON_API_VERSION = "2023-06-15"

WATSON_API_KEY = os.getenv("WATSON_API_KEY", "").strip()
WATSON_SERVICE_URL = os.getenv("WATSON_SERVICE_URL", "").strip()
ASSISTANT_ID = os.getenv("WATSON_ASSISTANT_ID", "").strip()

# Placeholders do .env.example não contam como credenciais válidas
_PLACEHOLDERS = {"sua_api_key_aqui", "seu_assistant_id_aqui", ""}


def watson_credentials_ok() -> bool:
    """Indica se há credenciais Watson utilizáveis no ambiente."""
    return (
        WATSON_API_KEY not in _PLACEHOLDERS
        and ASSISTANT_ID not in _PLACEHOLDERS
        and bool(WATSON_SERVICE_URL)
    )


def get_watson_client() -> AssistantV2:
    """Cria o cliente autenticado do Watson Assistant v2."""
    if not watson_credentials_ok():
        raise RuntimeError(
            "Credenciais do Watson ausentes ou incompletas. "
            "Preencha WATSON_API_KEY, WATSON_SERVICE_URL e WATSON_ASSISTANT_ID no .env."
        )

    authenticator = IAMAuthenticator(WATSON_API_KEY)
    assistant = AssistantV2(
        version=WATSON_API_VERSION,
        authenticator=authenticator,
    )
    assistant.set_service_url(WATSON_SERVICE_URL)
    return assistant
