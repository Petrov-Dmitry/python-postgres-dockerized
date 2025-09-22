import logging
import signal
import subprocess
import sys
import psutil

from core.args_parser import parse_args, setup_detached_mode, setup_log_level
from core.eetgbot import EeTgBot
from core.log_handler import LogsHandler
from core.models.logs import LogsModel
from core.models.settings import SettingsModel
from utils.migrations import MigrationManager

def setup_logger(log_level, detached_mode):
    """Настройка логирования."""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    log_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)s - %(levelname)s - %(message)s',
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

def _is_process_running(pid: int) -> bool:
    """Проверяет, существует ли процесс с заданным PID."""
    try:
        psutil.Process(pid)
        return True
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied:
        return True  # Процесс есть, но нет прав доступа
    except ValueError:
        return False  # Некорректный PID (например, отрицательный)

def prevent_multiple_instances():
    """Предотвращает повторный запуск программы."""
    saved_pid = SettingsModel().get('pid')
    if saved_pid and _is_process_running(int(saved_pid)):
        logging.warning(f"Another instance of EveEchoes Telegram Bot is already running with PID {saved_pid}. Exiting.")
        sys.exit(0)

def run_application():
    """Запуск приложения с обработкой сигналов."""
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))  # Ctrl+C
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0)) # Сигнал остановки машины

    bot = EeTgBot()
    try:
        bot.start()
    except Exception as e:
        logging.error(f"Application error: {e}")
        quit_application(bot)
        sys.exit(1)

def quit_application(bot: EeTgBot):
    """Корректное завершение приложения"""
    logging.warning("EveEchoes Telegram Bot is shutting down")

    # Сброс логов в файл перед завершением
    LogsModel().dump_logs()

    # Остановка и закрытие ассистента
    bot.stop()

    # Удаляем PID из настроек
    SettingsModel().set('pid', None)
    logging.debug("EveEchoes Telegram Bot has stopped")

def main():
    args = parse_args()
    detached_mode = setup_detached_mode(args)
    log_level = setup_log_level(args)

    logger = setup_logger(log_level, detached_mode)

    mode = 'DETACHED' if detached_mode == True else 'ATTACHED'
    logging.info(
        f"EveEchoes Telegram Bot launched in {mode} mode "
        f"with log-level {logging.getLevelName(int(logger.level))}"
    )

    prevent_multiple_instances()

    logging.debug("Update EveEchoes Telegram Bot database version")
    MigrationManager().apply_to_version(None)

    if detached_mode == True:
        python_exec = sys.executable
        detached_process = subprocess.Popen(
            [python_exec, "-c",
             f"from eeTgBot import run_application, setup_logger; run_application(setup_logger({log_level}, True))"],
            creationflags=0,
            start_new_session=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True
        )

        SettingsModel().set('pid', detached_process.pid)
        logging.debug(f"EveEchoes Telegram Bot in detached mode - console is free. PID: {detached_process.pid}")

        sys.exit(0)  # Корректное завершение основного процесса
    else:
        pid = psutil.Process().pid
        SettingsModel().set('pid', pid)
        logging.debug(f"EveEchoes Telegram Bot in attached mode - console is locked. PID: {pid}")

        run_application()

# self.migration_manager = MigrationManager(db_url)
if __name__ == "__main__":
    main()
