from pydantic_settings import BaseSettings, SettingsConfigDict


class PdfSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PDF_", env_file=".env", env_file_encoding="utf-8")

    s3_bucket: str = ""
    s3_region: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_prefix: str = "pdf/"


settings = PdfSettings()
