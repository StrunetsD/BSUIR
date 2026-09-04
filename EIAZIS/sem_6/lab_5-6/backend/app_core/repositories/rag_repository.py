import re

from psycopg2.extras import RealDictCursor

from ..db import get_db_connection


class RagRepository:
    def create_document(self, title: str, source: str | None, author: str | None, raw_text: str) -> dict:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO rag_documents (title, source, author, raw_text)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, title, source, author, created_at
                    """,
                    (title, source, author, raw_text),
                )
                row = cur.fetchone()
        return dict(row) if row else {}

    def create_chunk(self, document_id: int, chunk_index: int, chunk_text: str, point_id: str) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rag_chunks (document_id, chunk_index, chunk_text, qdrant_point_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (document_id, chunk_index, chunk_text, point_id),
                )

    def list_chunks_for_document(self, document_id: int, limit: int = 16) -> list[dict]:
        """Чанки одного документа по порядку — для вопросов с точным названием в кавычках."""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT d.id AS document_id, d.title, d.author, d.source,
                           c.chunk_index, c.chunk_text
                    FROM rag_chunks c
                    JOIN rag_documents d ON d.id = c.document_id
                    WHERE c.document_id = %s
                    ORDER BY c.chunk_index ASC
                    LIMIT %s
                    """,
                    (document_id, limit),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def get_chunk_with_doc(self, document_id: int, chunk_index: int) -> dict | None:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT d.id AS document_id, d.title, d.author, d.source, c.chunk_index, c.chunk_text
                    FROM rag_chunks c
                    JOIN rag_documents d ON d.id = c.document_id
                    WHERE c.document_id = %s AND c.chunk_index = %s
                    """,
                    (document_id, chunk_index),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def list_documents(self, limit: int = 100) -> list[dict]:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, title, author, source, created_at
                    FROM rag_documents
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def find_document_by_title(self, title_query: str) -> dict | None:
        pattern = f"%{title_query.strip()}%"
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, title, author, source, raw_text, created_at
                    FROM rag_documents
                    WHERE LOWER(title) LIKE LOWER(%s)
                    ORDER BY LENGTH(title) ASC, id DESC
                    LIMIT 1
                    """,
                    (pattern,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def _normalize_title_query(title_query: str) -> str:
        text = (title_query or "").strip().lower()
        text = text.strip("«»\"'“”‘’?")
        text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def find_document_by_title_candidates(self, *candidates: str) -> dict | None:
        seen: set[str] = set()
        ordered: list[str] = []
        for raw in candidates:
            if not raw:
                continue
            for variant in {raw.strip(), self._normalize_title_query(raw)}:
                if not variant or variant in seen:
                    continue
                seen.add(variant)
                ordered.append(variant)

        for title in ordered:
            doc = self.find_document_by_title(title)
            if doc:
                return doc
        return None

    def find_documents_by_author(self, author_query: str, limit: int = 10) -> list[dict]:
        pattern = f"%{author_query.strip()}%"
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, title, author, source, created_at
                    FROM rag_documents
                    WHERE author IS NOT NULL AND LOWER(author) LIKE LOWER(%s)
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (pattern, limit),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def search_raw_text(self, query: str, limit: int = 5) -> list[dict]:
        pattern = f"%{query.strip()}%"
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, title, author, source,
                           SUBSTRING(raw_text FROM 1 FOR 1500) AS excerpt
                    FROM rag_documents
                    WHERE LOWER(raw_text) LIKE LOWER(%s)
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (pattern, limit),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def list_authors(self, limit: int = 50) -> list[str]:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT author
                    FROM rag_documents
                    WHERE author IS NOT NULL AND author <> ''
                    ORDER BY author ASC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [row[0] for row in rows]

    def document_exists(self, title: str, author: str | None = None) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if author:
                    cur.execute(
                        """
                        SELECT 1
                        FROM rag_documents
                        WHERE LOWER(title) = LOWER(%s)
                          AND LOWER(COALESCE(author, '')) = LOWER(%s)
                        LIMIT 1
                        """,
                        (title.strip(), author.strip()),
                    )
                else:
                    cur.execute(
                        """
                        SELECT 1
                        FROM rag_documents
                        WHERE LOWER(title) = LOWER(%s)
                        LIMIT 1
                        """,
                        (title.strip(),),
                    )
                row = cur.fetchone()
        return bool(row)
