import os

from setuptools import setup, find_packages
from setuptools_scm import get_version

# Собираем список зависимостей
REQUIREMENTS_FILE = 'requirements.txt'
__requirements__ = []
if os.path.exists(REQUIREMENTS_FILE):
    with open(REQUIREMENTS_FILE) as f:
        __requirements__ = f.read().splitlines()
else:
    print(f"Файл зависимостей {REQUIREMENTS_FILE} не найден. Установка будет выполнена без зависимостей.")

# Генерация файла version.py
with open("version.py", "w") as f:
    version = get_version(
        version_scheme="post-release",      # Формат версии: 0.0.post5
        local_scheme="no-local-version",    # Игнорировать локальные изменения
    )
    f.write(f'__version__ = "{version}"\n')

setup(
    name = 'eeTgBot',
    use_scm_version = {
        "version_scheme": "post-release",   # Формат версии: 0.0.post5
        "local_scheme": "no-local-version", # Игнорировать локальные изменения
    },
    description = 'EveEchoes telegram bot',
    packages = find_packages(),
    python_requires = '>=3.11.5',
    install_requires = __requirements__,
    setup_requires = ['setuptools_scm'],
)
