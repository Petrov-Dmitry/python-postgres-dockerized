import logging
import time

from core.log_handler import LogsHandler
from core.models.logs import LogsModel

def setup_logging(log_level, detached_mode):
    """Настройка логирования."""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    log_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if not detached_mode:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)

    log_handler = LogsHandler(LogsModel())
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)

    return logger

while True:
    time.sleep(1)

# self.migration_manager = MigrationManager(db_url)
