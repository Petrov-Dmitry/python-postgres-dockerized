import argparse
from core.models.logs import LogsModel
from core.models.settings import SettingsModel
from version import __version__

def parse_args() -> argparse.Namespace:
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description=f"""EveEchoes Telegram Bot
Program version: {__version__}
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python eetgbot.py                    # Run in mode from settings
  python eetgbot.py -d                 # Run in detached mode
  python eetgbot.py --detached         # Run in detached mode (long form)
  python eetgbot.py -a                 # Run in attached mode (default)
  python eetgbot.py --attached         # Run in attached mode (long form)
  python eetgbot.py -v DEBUG           # Run with DEBUG log level
  python eetgbot.py --verbosity INFO   # Run with INFO log level (long form)
  python eetgbot.py -V                 # Show program version
  python eetgbot.py --version          # Show program version (long form)
  python eetgbot.py -h                 # Show this help message
  python eetgbot.py --help             # Show this help message (long form)
        """
    )

    # Группа режимов запуска
    run_mode = parser.add_mutually_exclusive_group()
    run_mode.add_argument(
        '-d', '--detached',
        action='store_true',
        help='Run in detached mode (do not hold console)'
    )
    run_mode.add_argument(
        '-a', '--attached',
        action='store_true',
        help='Run in attached mode (hold console)'
    )

    # Группа логирования
    parser.add_argument(
        '-v', '--verbosity',
        type=str,
        choices=LogsModel.get_log_levels().keys(),
        help=f'Log level: {", ".join(f"{name} = {value}" for name, value in LogsModel.get_log_levels().items())}'
    )

    # Информационные аргументы
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'EveEchoes Telegram Bot version: {__version__}',
        help='Show program version and exit'
    )

    return parser.parse_args()

def setup_detached_mode(args: argparse.Namespace) -> bool:
    """
    Определяет режим запуска на основе аргументов и настроек

    Args:
        args: Аргументы командной строки
        settings_detached: Значение из настроек

    Returns:
        bool: True если нужно запустить в detached mode
    """
    if args.detached:
        SettingsModel().set('detached_mode', True)
    else:
        SettingsModel().set('detached_mode', False)

    return SettingsModel().get('detached_mode')

def setup_log_level(args: argparse.Namespace) -> int:
    """
    Определяет уровень логирования на основе аргументов и настроек

    Args:
        args: Аргументы командной строки
        settings_level: Уровень логирования из настроек

    Returns:
        int: Уровень логирования
    """
    if args.verbosity:
        level = LogsModel.get_log_levels()[args.verbosity.upper()]
        LogsModel.set_log_level(level)

    return LogsModel.get_log_level()
