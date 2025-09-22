import logging
import time

from core.models.logs import LogsModel
from core.models.settings import SettingsModel

logger = logging.getLogger(__name__)

class EeTgBot:
    """Основной класс приложения"""
    def __init__(self):
        self.log_model = LogsModel()
        self.settings = SettingsModel()

    def start(self):
        """Запускает приложение"""
        logger.debug("EveEchoes Telegram Bot has started")
        while True:
            time.sleep(5)

    def stop(self):
        """Завершает работу приложения."""
        return True
