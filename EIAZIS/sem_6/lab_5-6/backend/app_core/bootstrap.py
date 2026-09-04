import time

from .config import get_settings
from .db import get_db_connection


def bootstrap_infrastructure() -> None:
    settings = get_settings()
    for attempt in range(1, settings.db_init_max_retries + 1):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS dialog_messages (
                            id SERIAL PRIMARY KEY,
                            user_text TEXT NOT NULL,
                            bot_text TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        );
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS rag_documents (
                            id SERIAL PRIMARY KEY,
                            title TEXT NOT NULL,
                            author TEXT,
                            source TEXT,
                            raw_text TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        );
                        """
                    )
                    cur.execute(
                        """
                        ALTER TABLE rag_documents
                        ADD COLUMN IF NOT EXISTS author TEXT;
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS rag_chunks (
                            id SERIAL PRIMARY KEY,
                            document_id INTEGER NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
                            chunk_index INTEGER NOT NULL,
                            chunk_text TEXT NOT NULL,
                            qdrant_point_id TEXT NOT NULL UNIQUE,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        );
                        """
                    )
            return
        except Exception:
            if attempt == settings.db_init_max_retries:
                raise
            time.sleep(settings.db_init_retry_delay)
