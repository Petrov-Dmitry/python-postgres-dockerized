import logging

from core.db_manager import DB_URL, DatabaseManager
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SettingsModel:
    """Модель для работы с настройками приложения."""
    def __init__(self, db_url: str = DB_URL):
        self.db_manager = DatabaseManager(db_url)

    def get(self, key):
        """Получает значение настройки по ключу."""
        result = self.db_manager.execute(
            'SELECT value FROM settings WHERE key = %s',
            (key),
            fetchone=True
        )
        return result[0] if result else None

    def set(self, key, value):
        """Устанавливает значение настройки по ключу."""
        result = self.db_manager.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (%s, %s)',
            (key, value)
        )
        logger.debug(f"SettingsModel.set({key}, {value})")
        return result

    def delete(self, key):
        """Удаляет значение настройки по ключу."""
        result = self.db_manager.execute(
            'DELETE FROM settings WHERE key = %s',
            (key)
        )
        logger.debug(f"SettingsModel.delete({key})")
        return result
