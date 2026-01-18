from __future__ import annotations

from typing import Any, Optional

from config import settings

_local_model: Optional[Any] = None


class LLMClient:
    def generate(self, prompt: str) -> str:
        if settings.llm_provider == "local":
            return self._generate_local(prompt)
        # Stub client: replace with real provider implementation.
        return "Stub response based on prompt."

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
