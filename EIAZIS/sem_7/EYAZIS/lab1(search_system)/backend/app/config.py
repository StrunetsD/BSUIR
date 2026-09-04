from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://ips:ips@db:5432/ips"
    llm_provider: str = "off"
    mistral_api_key: str | None = None
    mistral_chat_model: str = "ministral-14b-2512"
    mistral_embed_model: str = "mistral-embed"
    ollama_base_url: str = "http://ollama:11434"
    ollama_chat_model: str = "qwen2.5:3b"
    ollama_embed_model: str = "nomic-embed-text"
    search_top_k: int = 10
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
