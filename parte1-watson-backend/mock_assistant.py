"""
CardioIA - Fase 5, Cap 1
Assistente MOCK local (fallback técnico — seção 11 do plano).

Usado apenas quando o IBM Watson Assistant está indisponível (quota excedida,
instabilidade ou ausência de credenciais), para que a demonstração da interface
não fique bloqueada. As respostas reproduzem, de forma simplificada por
palavras-chave, os mesmos nós de diálogo modelados em `watson_skill.json` —
que continua sendo a modelagem real do assistente.
"""

import uuid

# Ordem importa: emergência é avaliada antes de qualquer outra regra,
# espelhando a prioridade do nó de emergência no dialog tree do Watson.
#
# Cada palavra-chave pode ser:
#   - uma string  → basta que ela apareça na mensagem;
#   - uma tupla   → todos os termos precisam aparecer (equivale ao encadeamento
#                   "#intent AND @entity" das condições do Watson).
REGRAS = [
    (
        "emergencia",
        ["infarto", "infartando", "ambulancia", "ambulância", "socorro",
         "emergencia", "emergência", "não consigo respirar", "nao consigo respirar",
         "coração parando", "coracao parando", "dor no peito forte", "desmaiando"],
        "🚨 EMERGÊNCIA DETECTADA! 🚨\n"
        "Ligue IMEDIATAMENTE para:\n"
        "• SAMU: 192\n"
        "• Bombeiros: 193\n"
        "• Pronto-socorro mais próximo\n"
        "Não aguarde atendimento virtual em situações de risco de vida.\n"
        "Você está em local seguro agora?",
        True,
    ),
    (
        "saudacao",
        ["ola", "olá", "oi", "bom dia", "boa tarde", "boa noite"],
        "Olá! Fico feliz em te atender. 😊\n"
        "Sou o CardioIA e posso ajudar com:\n"
        "• Informações sobre sintomas cardíacos\n"
        "• Orientações sobre pressão arterial e frequência cardíaca\n"
        "• Dúvidas sobre medicamentos (apenas informativas)\n"
        "• Indicação de quando buscar atendimento médico\n"
        "O que você gostaria de saber?",
        False,
    ),
    (
        "despedida",
        ["tchau", "até logo", "ate logo", "até mais", "ate mais", "encerrar"],
        "Foi um prazer ajudar! Lembre-se: cuide do seu coração. 🫀\n"
        "• Exercite-se regularmente\n"
        "• Mantenha alimentação equilibrada\n"
        "• Evite tabaco e álcool em excesso\n"
        "• Faça check-ups periódicos\n"
        "Em caso de emergência: SAMU 192. Até logo! 👋",
        False,
    ),
    (
        "relatar_sintoma",
        ["dor no peito", "aperto no peito", "dor torácica", "dor toracica",
         "braço esquerdo", "braco esquerdo"],
        "Dor no peito é um sintoma que merece atenção imediata. ⚠️\n"
        "Algumas perguntas importantes:\n"
        "• A dor é forte e constante ou leve e passageira?\n"
        "• Irradia para o braço, pescoço ou mandíbula?\n"
        "• Está acompanhada de falta de ar ou suor frio?\n"
        "Se a dor for forte e persistente, busque atendimento de emergência agora.\n"
        "Caso contrário, consulte um cardiologista o quanto antes.",
        False,
    ),
    (
        "relatar_sintoma",
        ["palpitação", "palpitacao", "palpitações", "palpitacoes",
         "coração acelerado", "coracao acelerado", "batimento irregular"],
        "Palpitações podem ser benignas ou indicar arritmias. 💓\n"
        "Observe: há quanto tempo você sente isso? Acontece em repouso ou esforço?\n"
        "É recomendado registrar episódios (horário, duração, atividade) e "
        "apresentar para um médico.\n"
        "Quer saber como medir sua frequência cardíaca?",
        False,
    ),
    (
        "relatar_sintoma",
        ["falta de ar", "dispneia", "dificuldade para respirar", "sem fôlego",
         "sem folego", "tontura", "vertigem", "fadiga", "cansaço", "cansaco"],
        "Sintomas como falta de ar, tontura e fadiga podem ter origem cardíaca. 🫁\n"
        "Sinais de alerta: surgirem em repouso, piorarem ao deitar ou virem "
        "acompanhados de inchaço nas pernas ou dor no peito.\n"
        "Se forem súbitos ou intensos, procure emergência. Se forem progressivos, "
        "agende avaliação com um cardiologista.",
        False,
    ),
    (
        "perguntar_pressao",
        [("press", "alta"), ("press", "elevada"), ("press", "subiu"), "hipertens"],
        "Pressão alta (hipertensão) é definida por valores ≥ 140/90 mmHg. 🔴\n"
        "Fatores de risco: obesidade, sedentarismo, dieta rica em sal, estresse.\n"
        "O tratamento inclui mudanças de estilo de vida e, quando necessário, medicação.\n"
        "Nunca interrompa medicamentos por conta própria. Consulte seu médico.",
        False,
    ),
    (
        "perguntar_pressao",
        [("press", "baixa"), ("press", "caiu"), "hipotens"],
        "Pressão baixa (hipotensão) é geralmente < 90/60 mmHg. 🔵\n"
        "Pode causar tontura, desmaio e fraqueza.\n"
        "Hidratação adequada e alimentação fracionada costumam ajudar.\n"
        "Se os sintomas forem frequentes, consulte um médico.",
        False,
    ),
    (
        "perguntar_pressao",
        ["pressão", "pressao", "mmhg"],
        "Os valores de referência para pressão arterial são:\n"
        "✅ Normal: até 120/80 mmHg\n"
        "⚠️ Pré-hipertensão: 121-139 / 81-89 mmHg\n"
        "🔴 Hipertensão Estágio 1: 140-159 / 90-99 mmHg\n"
        "🔴 Hipertensão Estágio 2: ≥ 160 / ≥ 100 mmHg\n"
        "As medições devem ser feitas em repouso, preferencialmente acompanhadas "
        "pelo médico.",
        False,
    ),
    (
        "perguntar_frequencia",
        ["bpm", "frequência cardíaca", "frequencia cardiaca", "batimento",
         "batimentos", "taquicardia", "bradicardia"],
        "A frequência cardíaca normal em adultos em repouso é de 60 a 100 BPM. ❤️\n"
        "• Atletas treinados: pode ser 40-60 BPM (normal para eles)\n"
        "• Taquicardia: > 100 BPM em repouso\n"
        "• Bradicardia: < 60 BPM (em não-atletas)\n"
        "Para medir: conte os batimentos em 15 segundos e multiplique por 4.\n"
        "Valores fora da faixa normal de forma persistente merecem avaliação médica.",
        False,
    ),
    (
        "perguntar_medicamento",
        ["remédio", "remedio", "medicament", "aspirina", "betabloqueador",
         "estatina", "losartana", "anticoagulante", "ieca"],
        "Posso compartilhar informações gerais sobre medicamentos cardíacos, "
        "mas é fundamental que qualquer medicação seja prescrita por um médico. 💊\n"
        "Classes comuns:\n"
        "• Betabloqueadores: controlam frequência e pressão\n"
        "• Estatinas: reduzem colesterol\n"
        "• Anticoagulantes: previnem coágulos\n"
        "• IECA/BRA: protegem coração e rins em hipertensos\n"
        "Sobre qual medicamento você gostaria de saber mais?",
        False,
    ),
    (
        "marcar_consulta",
        ["marcar consulta", "agendar", "consulta", "cardiologista", "médico",
         "medico"],
        "Para agendar consulta com cardiologista, você pode: 📅\n"
        "• Pelo SUS: procurar a UBS (Unidade Básica de Saúde) para encaminhamento\n"
        "• Plano de saúde: ligar para o número no verso do cartão\n"
        "• Particular: buscar no site da Sociedade Brasileira de Cardiologia (cardiol.br)\n"
        "Deseja saber quais sintomas indicam urgência no atendimento?",
        False,
    ),
    (
        "informacao_geral",
        ["o que é infarto", "o que e infarto", "arritmia", "insuficiência cardíaca",
         "insuficiencia cardiaca", "avc", "fatores de risco", "doenças do coração",
         "doencas do coracao"],
        "As doenças cardiovasculares são a principal causa de morte no Brasil e no mundo.\n"
        "As mais comuns incluem:\n"
        "🫀 Infarto do miocárdio: obstrução de artérias coronárias\n"
        "⚡ Arritmia: alteração no ritmo cardíaco\n"
        "💧 Insuficiência cardíaca: o coração não bombeia sangue suficientemente\n"
        "🧠 AVC: interrupção do fluxo sanguíneo cerebral\n"
        "Fatores de risco modificáveis: tabagismo, sedentarismo, obesidade, "
        "dieta inadequada.\n"
        "Sobre qual condição gostaria de mais detalhes?",
        False,
    ),
    (
        "ajuda",
        ["ajuda", "menu", "o que você faz", "o que voce faz", "como você funciona",
         "como voce funciona", "opções", "opcoes"],
        "Posso te ajudar com: 🆘\n"
        "1️⃣ Relatar sintomas → te oriento sobre urgência\n"
        "2️⃣ Pressão arterial → valores de referência e orientações\n"
        "3️⃣ Frequência cardíaca → o que é normal\n"
        "4️⃣ Medicamentos → informações gerais (nunca prescrevendo)\n"
        "5️⃣ Agendar consulta → como e onde buscar atendimento\n"
        "6️⃣ Informações gerais → doenças e fatores de risco\n"
        "Digite sua dúvida em linguagem natural. Estou aqui! 😊",
        False,
    ),
]

FALLBACK = (
    "nao_entendeu",
    "Desculpe, não entendi bem. 🤔\n"
    "Posso ajudar com sintomas, pressão arterial, frequência cardíaca, "
    "medicamentos ou informações gerais sobre saúde cardíaca.\n"
    "Tente reformular sua pergunta ou digite 'ajuda' para ver as opções.",
    False,
)

BOAS_VINDAS = (
    "Olá! Sou o CardioIA, seu assistente cardiológico virtual. 🫀\n"
    "Posso ajudar com informações sobre sintomas, pressão arterial, "
    "frequência cardíaca e orientações gerais de saúde.\n"
    "⚠️ Atenção: não substituo consulta médica. Em emergências, ligue 192 (SAMU).\n"
    "Como posso ajudar hoje?"
)


def create_session() -> str:
    """Gera um identificador de sessão local (equivalente ao session_id Watson)."""
    return f"mock-{uuid.uuid4()}"


def _casa(texto: str, palavra_chave) -> bool:
    """Verifica uma palavra-chave simples (string) ou composta (tupla de termos)."""
    if isinstance(palavra_chave, tuple):
        return all(termo in texto for termo in palavra_chave)
    return palavra_chave in texto


def message(texto: str) -> dict:
    """Classifica a mensagem por palavras-chave e devolve a resposta correspondente."""
    t = texto.lower().strip()

    for intent, palavras_chave, resposta, emergencia in REGRAS:
        if any(_casa(t, kw) for kw in palavras_chave):
            return {"response": resposta, "intent": intent, "is_emergency": emergencia}

    intent, resposta, emergencia = FALLBACK
    return {"response": resposta, "intent": intent, "is_emergency": emergencia}
