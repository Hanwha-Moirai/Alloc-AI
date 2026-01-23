from __future__ import annotations

from typing import Any, Optional

from config import settings

_local_model: Optional[Any] = None
_openai_client: Optional[Any] = None
_gemini_model: Optional[Any] = None


class LLMClient:
    def generate(self, prompt: str) -> str:
        if settings.llm_provider == "gemini":
            return self._generate_gemini(prompt)
        if settings.llm_provider == "openai":
            return self._generate_openai(prompt)
        if settings.llm_provider == "local":
            return self._generate_local(prompt)
        # Stub client: replace with real provider implementation.
        return "Stub response based on prompt."

    def _generate_gemini(self, prompt: str) -> str:
        if not settings.gemini_api_key:
            raise ValueError("RAG_GEMINI_API_KEY must be set for Gemini usage.")
        model = self._get_gemini_model()
        response = model.generate_content(prompt)
        return response.text or ""

    def _generate_openai(self, prompt: str) -> str:
        if not settings.openai_api_key:
            raise ValueError("RAG_OPENAI_API_KEY must be set for OpenAI usage.")
        client = self._get_openai_client()
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
        )
        return response.choices[0].message.content or ""

    def _generate_local(self, prompt: str) -> str:
        if not settings.llm_model_path:
            raise ValueError("RAG_LLM_MODEL_PATH must be set for local LLM usage.")
        model = self._get_local_model()
        response = model(
            prompt,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
        )
        return response["choices"][0]["text"]

    def _get_local_model(self) -> Any:
        global _local_model
        if _local_model is None:
            try:
                from llama_cpp import Llama
            except ImportError as exc:
                raise RuntimeError(
                    "llama-cpp-python is required for local LLM. Install it and retry."
                ) from exc
            _local_model = Llama(
                model_path=settings.llm_model_path,
                n_ctx=settings.max_context_tokens,
            )
        return _local_model

    def _get_openai_client(self) -> Any:
        global _openai_client
        if _openai_client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError("openai package is required for OpenAI usage. Install it and retry.") from exc
            client_kwargs = {"api_key": settings.openai_api_key}
            if settings.openai_base_url:
                client_kwargs["base_url"] = settings.openai_base_url
            _openai_client = OpenAI(**client_kwargs)
        return _openai_client

    def _get_gemini_model(self) -> Any:
        global _gemini_model
        if _gemini_model is None:
            try:
                import google.generativeai as genai
            except ImportError as exc:
                raise RuntimeError(
                    "google-generativeai is required for Gemini usage. Install it and retry."
                ) from exc
            genai.configure(api_key=settings.gemini_api_key)
            _gemini_model = genai.GenerativeModel(settings.gemini_model)
        return _gemini_model
