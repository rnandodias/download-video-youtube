import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
}

_PROMPT = """\
Você é um especialista em análise de conteúdo e criação de resumos detalhados.

A transcrição abaixo foi detectada no idioma: {language}

Sua tarefa:
{translation_instruction}\
- Gere um resumo detalhado em português, organizado por tópicos com marcadores \
quando apropriado, cobrindo os principais pontos, argumentos e conclusões.

Use exatamente este formato na resposta:
{translation_header}\
## Resumo Detalhado

[resumo aqui]

---

Transcrição:
{transcript}"""


def _build_prompt(transcript: str, language: str) -> str:
    needs_translation = language not in ("pt",)
    if needs_translation:
        translation_instruction = (
            "- Forneça primeiro uma tradução completa para o português.\n"
        )
        translation_header = "## Tradução para o Português\n\n[tradução aqui]\n\n"
    else:
        translation_instruction = ""
        translation_header = ""
    return _PROMPT.format(
        language=language,
        translation_instruction=translation_instruction,
        translation_header=translation_header,
        transcript=transcript,
    )


def summarize(
    transcript: str,
    language: str,
    provider: str,
    model: Optional[str] = None,
) -> str:
    """
    Gera tradução (quando necessário) e resumo detalhado usando o provedor escolhido.

    Args:
        transcript: Texto transcrito.
        language:   Código do idioma detectado pelo Whisper (ex: 'en', 'pt').
        provider:   Provedor de IA: 'anthropic', 'openai' ou 'gemini'.
        model:      Modelo específico. Se None, usa o padrão do provedor.

    Returns:
        Resposta da IA com tradução (se necessário) e resumo.
    """
    effective_model = model or DEFAULT_MODELS[provider]
    prompt = _build_prompt(transcript, language)

    if provider == "anthropic":
        return _call_anthropic(prompt, effective_model)
    if provider == "openai":
        return _call_openai(prompt, effective_model)
    if provider == "gemini":
        return _call_gemini(prompt, effective_model)

    raise ValueError(
        f"Provedor '{provider}' desconhecido. Use: anthropic, openai, gemini"
    )


def _call_anthropic(prompt: str, model: str) -> str:
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY não encontrada no .env")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_openai(prompt: str, model: str) -> str:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY não encontrada no .env")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    return response.choices[0].message.content


def _call_gemini(prompt: str, model: str) -> str:
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY não encontrada no .env")

    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel(model)
    response = gemini_model.generate_content(prompt)
    return response.text
