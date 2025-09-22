import logging
import time

from core.log_handler import LogsHandler
from core.models.logs import LogsModel
from core.models.settings import SettingsModel

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

def main():
    while True:
        time.sleep(5)
    # args = parse_args()
    # settings = SettingsModel()
    # detached_mode = get_detached_mode(args, settings.get_detached_mode())
    # log_level = get_log_level(args, settings.get_log_level())

    # if args.verbosity is not None:
    #     settings.set_log_level(log_level)

    # logger = setup_logging(log_level, detached_mode)

    # mode = 'DETACHED' if detached_mode else 'ATTACHED'
    # logging.info(
    #     f"Local Voice Assistant (LVA) launched in {mode} mode "
    #     f"with log-level {logging.getLevelName(int(logger.level))}"
    # )

    # prevent_multiple_instances()

    # if detached_mode:
    #     # Используем pythonw.exe на Windows
    #     python_exec = sys.executable
    #     if system() == "Windows":
    #         python_exec = python_exec.replace("python.exe", "pythonw.exe")

    #     detached_process = subprocess.Popen(
    #         [python_exec, "-c",
    #          f"from lva import run_application, setup_logging; run_application(setup_logging({log_level}, True))"],
    #         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW if system() == "Windows" else 0,
    #         start_new_session=True,
    #         stdin=subprocess.PIPE,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE,
    #         close_fds=True
    #     )

    #     Settings().set_pid(detached_process.pid)
    #     logging.debug(f"LVA in detached mode. Console is free. PID: {detached_process.pid}")

    #     sys.exit(0)  # Корректное завершение основного процесса
    # else:
    #     pid = psutil.Process().pid
    #     Settings().set_pid(pid)
    #     logging.debug(f"LVA in attached mode. Console is locked. PID: {pid}")

    #     run_application(logger)

# self.migration_manager = MigrationManager(db_url)
if __name__ == "__main__":
    main()
