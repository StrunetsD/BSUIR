import time

import psycopg2
from psycopg2.extras import DictCursor
import logging

logger = logging.getLogger(__name__)


class DataService:
    def __init__(self, db_config):
        self.db_config = db_config
        self.init_database()

    def get_connection(self):
        return psycopg2.connect(**self.db_config)

    def init_database(self):
        """Инициализация таблиц БД с пересозданием всех таблиц"""
        drop_queries = [
            "DROP TABLE IF EXISTS document_terms CASCADE",
            "DROP TABLE IF EXISTS terms CASCADE",
            "DROP TABLE IF EXISTS documents CASCADE"
        ]

        # Затем создаем таблицы заново
        create_queries = [
            """
            CREATE TABLE documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                date_added DATE DEFAULT CURRENT_DATE,
                file_path TEXT UNIQUE NOT NULL,
                last_modified FLOAT,
                doc_length INTEGER
            )
            """,
            """
            CREATE TABLE terms (
                term VARCHAR(255) PRIMARY KEY,
                doc_count INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE document_terms (
                doc_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                term VARCHAR(255) REFERENCES terms(term) ON DELETE CASCADE,
                frequency INTEGER NOT NULL,
                PRIMARY KEY (doc_id, term)
            )
            """
        ]

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Удаляем существующие таблицы
                    logger.info("Удаление существующих таблиц...")
                    for query in drop_queries:
                        cur.execute(query)

                    # Создаем таблицы заново
                    logger.info("Создание новых таблиц...")
                    for query in create_queries:
                        cur.execute(query)

                    conn.commit()
                    logger.info("База данных успешно переинициализирована")

        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    def add_document(self, title, content, file_path, last_modified, doc_length):
        """Добавление документа в БД"""
        query = """
            INSERT INTO documents (title, content, file_path, last_modified, doc_length)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (file_path) 
            DO UPDATE SET 
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                last_modified = EXCLUDED.last_modified,
                doc_length = EXCLUDED.doc_length
            RETURNING id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (title, content, file_path, last_modified, doc_length))
                    doc_id = cur.fetchone()[0]
                    conn.commit()
                    return doc_id
        except Exception as e:
            logger.error(f"Ошибка добавления документа: {e}")
            raise

    def delete_document(self, file_path):
        """Удаление документа по file_path с правильным обновлением статистики терминов"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    with conn.cursor() as cur:
                        # Use lower isolation level and explicit locking
                        cur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")

                        # Get document ID with lock
                        cur.execute("SELECT id FROM documents WHERE file_path = %s FOR UPDATE", (file_path,))
                        result = cur.fetchone()
                        if not result:
                            logger.info(f"Document not found, skipping deletion: {file_path}")
                            return True  # Document already doesn't exist

                        doc_id = result[0]

                        # Get terms for this document BEFORE deletion
                        cur.execute("SELECT term FROM document_terms WHERE doc_id = %s", (doc_id,))
                        terms = [row[0] for row in cur.fetchall()]
                        logger.info(f"Found {len(terms)} terms to update for document {file_path}")

                        # Delete document (cascades to document_terms)
                        cur.execute("DELETE FROM documents WHERE file_path = %s", (file_path,))

                        # Update term counts in alphabetical order to prevent deadlocks
                        if terms:
                            sorted_terms = sorted(terms)
                            for term in sorted_terms:
                                # Decrement document count for each term
                                cur.execute("""
                                    UPDATE terms 
                                    SET doc_count = doc_count - 1 
                                    WHERE term = %s
                                """, (term,))

                                # Check if update was successful
                                if cur.rowcount == 0:
                                    logger.warning(f"Term {term} not found in terms table during deletion")

                            # Remove terms with zero or negative count
                            cur.execute("DELETE FROM terms WHERE doc_count <= 0")
                            zero_terms_deleted = cur.rowcount
                            if zero_terms_deleted > 0:
                                logger.info(f"Removed {zero_terms_deleted} terms with zero document count")

                        conn.commit()
                        logger.info(f"Successfully deleted document and updated terms: {file_path}")
                        return True

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to delete {file_path}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed to delete {file_path}: {e}")
                    return False
                time.sleep(0.5 * (attempt + 1))  # Backoff

    def get_document_by_path(self, file_path):
        """Получение документа по пути"""
        query = "SELECT * FROM documents WHERE file_path = %s"
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute(query, (file_path,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения документа: {e}")
            return None

    def update_term_stats(self, term_frequencies):
        """Обновление статистики терминов"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Обновление счетчиков документов для терминов
                    for term in term_frequencies.keys():
                        cur.execute("""
                            INSERT INTO terms (term, doc_count) 
                            VALUES (%s, 1)
                            ON CONFLICT (term) 
                            DO UPDATE SET doc_count = terms.doc_count + 1
                        """, (term,))

                    conn.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления статистики терминов: {e}")
            raise

    def add_document_terms(self, doc_id, term_frequencies):
        """Добавление терминов документа с улучшенной обработкой конкурентности"""
        if not term_frequencies:
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    with conn.cursor() as cur:
                        # Use READ COMMITTED isolation level
                        cur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")

                        # Delete existing terms in batches if there are many
                        cur.execute("DELETE FROM document_terms WHERE doc_id = %s", (doc_id,))

                        # Insert new terms in alphabetical order
                        sorted_terms = sorted(term_frequencies.items())
                        batch_size = 100
                        for i in range(0, len(sorted_terms), batch_size):
                            batch = sorted_terms[i:i + batch_size]
                            values = [(doc_id, term, freq) for term, freq in batch]
                            args = ','.join(cur.mogrify("(%s,%s,%s)", x).decode('utf-8') for x in values)
                            cur.execute(f"""
                                INSERT INTO document_terms (doc_id, term, frequency) 
                                VALUES {args}
                                ON CONFLICT (doc_id, term) 
                                DO UPDATE SET frequency = EXCLUDED.frequency
                            """)

                        conn.commit()
                        logger.debug(f"Successfully added {len(term_frequencies)} terms for document {doc_id}")
                        return

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for document {doc_id}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed for document {doc_id}: {e}")
                    raise
                time.sleep(0.5 * (attempt + 1))

    def get_document_count(self):
        """Получение общего количества документов"""
        query = "SELECT COUNT(*) FROM documents"
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Ошибка получения количества документов: {e}")
            return 0

    def get_avg_doc_length(self):
        """Получение средней длины документов"""
        query = "SELECT AVG(doc_length) FROM documents WHERE doc_length IS NOT NULL"
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    result = cur.fetchone()[0]
                    return float(result) if result else 0.0
        except Exception as e:
            logger.error(f"Ошибка получения средней длины документов: {e}")
            return 0.0

    def get_term_doc_count(self, term):
        """Получение количества документов, содержащих термин"""
        query = "SELECT doc_count FROM terms WHERE term = %s"
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (term,))
                    result = cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка получения doc_count для термина {term}: {e}")
            return 0

    def get_document_terms(self, doc_id):
        """Получение терминов документа"""
        query = "SELECT term, frequency FROM document_terms WHERE doc_id = %s"
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (doc_id,))
                    return dict(cur.fetchall())
        except Exception as e:
            logger.error(f"Ошибка получения терминов документа {doc_id}: {e}")
            return {}

    def get_all_documents(self):
        """Получение всех документов"""
        query = "SELECT id, file_path, last_modified FROM documents"
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения документов: {e}")
            return []

    def get_document_by_id(self, doc_id):
        """Получение документа по ID"""
        query = "SELECT * FROM documents WHERE id = %s"
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute(query, (doc_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения документа по ID {doc_id}: {e}")
            return None

