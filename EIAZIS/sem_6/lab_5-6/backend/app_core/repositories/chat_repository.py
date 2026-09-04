from psycopg2.extras import RealDictCursor

from ..db import get_db_connection


class ChatRepository:
    def save_pair(self, user_text: str, bot_text: str) -> dict:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO dialog_messages (user_text, bot_text)
                    VALUES (%s, %s)
                    RETURNING id, user_text, bot_text, created_at
                    """,
                    (user_text, bot_text),
                )
                row = cur.fetchone()
        return dict(row) if row else {}

    def list_messages(self, limit: int) -> list[dict]:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, user_text, bot_text, created_at
                    FROM dialog_messages
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def get_recent_history(self, limit: int) -> list[dict]:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, user_text, bot_text, created_at
                    FROM dialog_messages
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def clear(self) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM dialog_messages")

    def truncate(self, keep: int) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM dialog_messages
                    WHERE id IN (
                        SELECT id FROM dialog_messages
                        ORDER BY id DESC
                        OFFSET %s
                    )
                    """,
                    (keep,),
                )

    def edit(self, message_id: int, user_text: str, bot_text: str) -> dict | None:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE dialog_messages
                    SET user_text = %s, bot_text = %s
                    WHERE id = %s
                    RETURNING id, user_text, bot_text, created_at
                    """,
                    (user_text, bot_text, message_id),
                )
                row = cur.fetchone()
        return dict(row) if row else None
