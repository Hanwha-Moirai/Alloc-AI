from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings

_llm: ChatGoogleGenerativeAI | None = None


def get_gemini_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        if not settings.gemini_api_key:
            raise ValueError("RAG_GEMINI_API_KEY must be set for Gemini usage.")
        _llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout_seconds,
        )
    return _llm
