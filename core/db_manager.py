import logging
import os
import psycopg2

from contextlib import contextmanager

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_url: str = DB_URL):
        self.db_url = db_url

    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для получения соединения с PostgreSQL."""
        conn = psycopg2.connect(self.db_url)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def _get_cursor(self, conn):
        """Контекстный менеджер для получения курсора PostgreSQL."""
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def execute(self, query, params=(), fetchone=False, fetchall=False):
        """Выполняет SQL-запрос и возвращает результат."""
        with self._get_connection() as conn:
            with self._get_cursor(conn) as cursor:
                cursor.execute(query, params)
                if fetchone:
                    return cursor.fetchone()
                if fetchall:
                    return cursor.fetchall()
                conn.commit()
