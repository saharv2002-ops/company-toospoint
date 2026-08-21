from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://churnscope:churnscope_dev@localhost:5432/churnscope"
    max_ingest_payload_bytes: int = 10 * 1024 * 1024  # 10 MB
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
