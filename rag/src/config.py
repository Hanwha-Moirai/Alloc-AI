from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_")

    app_name: str = "rag"
    environment: str = "dev"

    # Vector store
    vector_provider: str = "qdrant"

    # Retrieval knobs
    top_k: int = 5
    rerank_k: int = 10

    # LLM
    llm_provider: str = "stub"
    max_context_tokens: int = 2048


settings = Settings()
