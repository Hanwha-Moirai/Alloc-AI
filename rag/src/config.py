from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", env_file_encoding="utf-8")

    app_name: str = "rag"
    environment: str = "dev"

    # Vector store
    vector_provider: str = "qdrant"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # Retrieval knobs
    top_k: int = 5
    rerank_k: int = 10

    # LLM
    llm_provider: str = "stub"
    llm_model_path: str = ""
    llm_max_tokens: int = 512
    llm_temperature: float = 0.2
    max_context_tokens: int = 2048

    # MariaDB
    mariadb_host: str = "localhost"
    mariadb_port: int = 3306
    mariadb_user: str = ""
    mariadb_password: str = ""
    mariadb_database: str = ""


settings = Settings()
