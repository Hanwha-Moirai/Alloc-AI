from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", env_file_encoding="utf-8")

    app_name: str = "rag"
    environment: str = "dev"
    data_dir: str = str(Path(__file__).resolve().parents[1] / "data")

    # Vector store
    vector_provider: str = "qdrant"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "rag_chunks"

    # Retrieval knobs
    top_k: int = 5
    rerank_k: int = 10

    # LLM
    llm_provider: str = "stub"
    llm_model_path: str = ""
    llm_max_tokens: int = 512
    llm_temperature: float = 0.2
    max_context_tokens: int = 2048
    llm_timeout_seconds: int = 30
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # MariaDB
    mariadb_host: str = "localhost"
    mariadb_port: int = 3306
    mariadb_user: str = ""
    mariadb_password: str = ""
    mariadb_database: str = ""


settings = Settings()
