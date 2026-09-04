import psycopg2

from .config import get_settings


def get_db_connection():
    settings = get_settings()
    return psycopg2.connect(settings.database_url)
