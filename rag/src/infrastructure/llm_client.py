from __future__ import annotations

import logging
import time as time_module
from typing import Any, Optional

import requests

from config import settings

_local_model: Optional[Any] = None
_openai_client: Optional[Any] = None
_gemini_client: Optional[Any] = None

logger = logging.getLogger(__name__)


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
        timeout_s = settings.llm_timeout_seconds
        logger.info(
            "Gemini request start model=%s prompt_chars=%d timeout_s=%s",
            settings.gemini_model,
            len(prompt),
            timeout_s,
        )
        started = time_module.perf_counter()
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent"
        )
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": settings.gemini_api_key,
        }
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
            response.raise_for_status()
        except requests.Timeout as exc:
            logger.warning("Gemini request timeout after %s seconds", timeout_s)
            raise TimeoutError("Gemini request timed out.") from exc
        finally:
            elapsed = time_module.perf_counter() - started
            logger.info("Gemini request end elapsed_ms=%.2f", elapsed * 1000)

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return ""
        return parts[0].get("text", "") or ""

    def _generate_openai(self, prompt: str) -> str:
        if not settings.openai_api_key:
            raise ValueError("RAG_OPENAI_API_KEY must be set for OpenAI usage.")
        client = self._get_openai_client()
        logger.info("OpenAI request start model=%s prompt_chars=%d", settings.openai_model, len(prompt))
        started = time_module.perf_counter()
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
        )
        elapsed = time_module.perf_counter() - started
        logger.info("OpenAI request end elapsed_ms=%.2f", elapsed * 1000)
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

    def _get_gemini_client(self) -> Any:
        global _gemini_client
        if _gemini_client is None:
            try:
                from google import genai
            except ImportError as exc:
                raise RuntimeError(
                    "google-genai is required for Gemini usage. Install it and retry."
                ) from exc
            _gemini_client = genai.Client(api_key=settings.gemini_api_key)
        return _gemini_client
