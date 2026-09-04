from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://literature:literature@db:5432/literature_lab6",
        alias="DATABASE_URL",
    )
    qdrant_url: str = Field(default="http://qdrant:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="literature_chunks", alias="QDRANT_COLLECTION")
    ollama_base_url: str = Field(default="http://host.docker.internal:11434", alias="OLLAMA_BASE_URL")
    ollama_chat_model: str = Field(default="qwen2.5:7b-instruct", alias="OLLAMA_CHAT_MODEL")
    ollama_embed_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL")
    rag_chunk_size: int = Field(default=700, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=120, alias="RAG_CHUNK_OVERLAP")
    chat_history_limit: int = Field(default=6, alias="CHAT_HISTORY_LIMIT")
    chat_top_k: int = Field(default=4, alias="CHAT_TOP_K")
    sql_router_min_confidence: float = Field(default=0.85, alias="SQL_ROUTER_MIN_CONFIDENCE")
    db_init_max_retries: int = Field(default=30, alias="DB_INIT_MAX_RETRIES")
    db_init_retry_delay: float = Field(default=1.5, alias="DB_INIT_RETRY_DELAY")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
