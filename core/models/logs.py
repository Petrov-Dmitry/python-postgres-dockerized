import logging
import os

from core.db_manager import DB_URL, DatabaseManager
from core.models.settings import SettingsModel
from datetime import datetime

logger = logging.getLogger(__name__)

class LogsModel:
    """Модель для работы с логами."""
    def __init__(self, db_url: str = DB_URL):
        self.db_manager = DatabaseManager(db_url)
        self.settings = SettingsModel(db_url)

    @staticmethod
    def get_log_levels():
        """Возвращает словарь с уровнями логирования из модуля logging."""
        _nameToLevel = {value: key for key, value in logging._levelToName.items()}
        return {name: value for name, value in _nameToLevel.items() if name.isupper() and value > 0}

    def get_log_level(self):
        """Получает уровень логирования из базы данных."""
        level = self.settings.get('log_level')
        return int(level) if level else logging.DEBUG  # По умолчанию DEBUG

    def set_log_level(self, level):
        """Устанавливает уровень логирования в базу данных."""
        self.settings.set('log_level', str(level))
        logger.info(f"Log level set to {logging.getLevelName(int(level))}")

    def log_message(self, level, message):
        """Записывает сообщение в таблицу логов."""
        self.db_manager.execute(
            'INSERT INTO logs (level, message) VALUES (%s, %s)',
            (level, message)
        )

    def get_logs(self):
        """Возвращает все логи из таблицы, отсортированные по возрастанию времени."""
        return self.db_manager.execute(
            'SELECT timestamp, level, message FROM logs ORDER BY timestamp ASC',
            fetchall=True
        )

    def dump_logs(self):
        """Пишет логи из базы в файл в директории logs"""
        # Создаем директорию logs, если она не существует
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Формируем путь к файлу лога
        log_file_name = os.path.join(logs_dir, datetime.now().strftime("%Y%m%d%H%M%S") + '.log')
        logs = self.get_logs()

        with open(log_file_name, "w") as f:
            for log in logs:
                timestamp, level, message = log
                formatted_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                f.write(f"[{formatted_time}] {logging.getLevelName(int(level))}: {message}\n")

        logger.debug(f"All logs are dumped to file {log_file_name}")

    def clear_logs(self):
        """Очищает таблицу логов."""
        self.db_manager.execute('DELETE FROM logs')
        logger.debug("All logs are cleared!")
