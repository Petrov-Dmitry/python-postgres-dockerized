
import logging

from core.models.logs import LogsModel
from datetime import datetime

class LogsHandler(logging.Handler):
    """Логирование в базу данных."""
    def __init__(self, log_model: LogsModel):
        super().__init__()
        self.log_model = log_model

    def emit(self, record):
        level = record.levelno  # Числовой уровень логирования
        message = record.getMessage()
        self.log_model.log_message(level, message)
