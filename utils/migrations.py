"""
Database migrations package for PostgreSQL
"""
import psycopg2
import logging
from dataclasses import dataclass
from typing import List
from contextlib import contextmanager
import os
from datetime import datetime
import re

logger = logging.getLogger(__name__)

@dataclass
class Migration:
    """Класс, представляющий миграцию базы данных."""
    version: int
    up_sql: str
    down_sql: str

class MigrationManager:
    """Менеджер миграций базы данных PostgreSQL."""

    def __init__(self, db_url: str, migrations_dir: str = "migrations"):
        self.db_url = db_url
        self.migrations_dir = migrations_dir
        self._ensure_migrations_table()
        self._ensure_migrations_dir()

    def _ensure_migrations_dir(self):
        """Создает директорию для миграций, если она не существует."""
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            logger.info(f"Created migrations directory: {self.migrations_dir}")

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
        """Контекстный менеджер для получения курсора."""
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def _ensure_migrations_table(self):
        """Создает таблицу для отслеживания миграций, если она не существует."""
        with self._get_connection() as conn:
            with self._get_cursor(conn) as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()

    def get_current_version(self) -> int:
        """Возвращает текущую версию базы данных."""
        with self._get_connection() as conn:
            with self._get_cursor(conn) as cursor:
                cursor.execute("SELECT MAX(version) FROM migrations")
                result = cursor.fetchone()
                return result[0] or 0 if result else 0

    def get_applied_versions(self) -> List[int]:
        """Возвращает список применённых версий миграций."""
        with self._get_connection() as conn:
            with self._get_cursor(conn) as cursor:
                cursor.execute("SELECT version FROM migrations ORDER BY version")
                result = cursor.fetchall()
                return [row[0] for row in result]

    def apply_migration(self, migration: Migration):
        """Применяет миграцию."""
        current_version = self.get_current_version()

        if migration.version <= current_version:
            logger.info(f"Migration {migration.version} already applied")
            return False

        with self._get_connection() as conn:
            try:
                with self._get_cursor(conn) as cursor:
                    logger.info(f"Applying migration {migration.version}")

                    # Выполняем SQL команды миграции
                    cursor.execute(migration.up_sql)

                    # Сохраняем информацию о примененной миграции
                    cursor.execute(
                        "INSERT INTO migrations (version) VALUES (%s)",
                        (migration.version,)
                    )

                    conn.commit()
                    logger.info(f"Successfully applied migration {migration.version}")
                    return True

            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to apply migration {migration.version}: {e}")
                raise

    def rollback_migration(self, migration: Migration):
        """Откатывает миграцию."""
        applied_versions = self.get_applied_versions()

        if migration.version not in applied_versions:
            logger.info(f"Migration {migration.version} not applied")
            return False

        with self._get_connection() as conn:
            try:
                with self._get_cursor(conn) as cursor:
                    logger.info(f"Rolling back migration {migration.version}")

                    # Выполняем SQL команды отката
                    cursor.execute(migration.down_sql)

                    # Удаляем запись о миграции
                    cursor.execute(
                        "DELETE FROM migrations WHERE version = %s",
                        (migration.version,)
                    )

                    conn.commit()
                    logger.info(f"Successfully rolled back migration {migration.version}")
                    return True

            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to roll back migration {migration.version}: {e}")
                raise

    def apply_all_migrations(self, migrations: List[Migration]):
        """Применяет все миграции по порядку."""
        migrations.sort(key=lambda m: m.version)
        current_version = self.get_current_version()

        for migration in migrations:
            if migration.version > current_version:
                self.apply_migration(migration)

    def rollback_to_version(self, target_version: int, migrations: List[Migration]):
        """Откатывает миграции до указанной версии."""
        applied_versions = self.get_applied_versions()
        migrations_dict = {m.version: m for m in migrations}

        # Откатываем миграции в обратном порядке
        for version in sorted(applied_versions, reverse=True):
            if version > target_version and version in migrations_dict:
                self.rollback_migration(migrations_dict[version])

    def generate_migration_template(self, name: str, description: str = "") -> str:
        """
        Генерирует шаблонный файл миграции.

        Args:
            name: Название миграции (будет преобразовано в snake_case)
            description: Описание миграции (необязательно)

        Returns:
            Путь к созданному файлу миграции
        """
        # Получаем следующую версию миграции
        current_version = self.get_current_version()
        next_version = current_version + 1

        # Преобразуем имя в snake_case
        snake_case_name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        snake_case_name = re.sub(r'[^a-z0-9_]', '_', snake_case_name)
        snake_case_name = re.sub(r'_+', '_', snake_case_name).strip('_')

        # Создаем имя файла с timestamp для уникальности
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{next_version:04d}_{snake_case_name}.sql"
        filepath = os.path.join(self.migrations_dir, filename)

        # Шаблон миграции
        template = f"""-- Migration: {next_version:04d}_{snake_case_name}
-- Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Description: {description or 'No description provided'}

-- UP migration
/*
Ваш SQL код для применения миграции
Пример:
CREATE TABLE example_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
*/

-- DOWN migration
/*
Ваш SQL код для отката миграции
Пример:
DROP TABLE IF EXISTS example_table;
*/
"""

        # Создаем файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)

        logger.info(f"Generated migration template: {filepath}")
        return filepath

    def load_migrations_from_dir(self) -> List[Migration]:
        """
        Загружает все миграции из директории.

        Returns:
            Список объектов Migration, отсортированный по версии
        """
        migrations = []

        if not os.path.exists(self.migrations_dir):
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return migrations

        # Ищем все SQL файлы в директории
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.sql'):
                # Парсим версию из имени файла (первые цифры до первого _)
                match = re.match(r'^(\d+)', filename)
                if match:
                    try:
                        version = int(match.group(1))
                        filepath = os.path.join(self.migrations_dir, filename)

                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Парсим UP и DOWN секции
                        up_sql = self._extract_sql_section(content, 'UP migration')
                        down_sql = self._extract_sql_section(content, 'DOWN migration')

                        migrations.append(Migration(version, up_sql, down_sql))

                    except (ValueError, Exception) as e:
                        logger.warning(f"Failed to parse migration file {filename}: {e}")

        # Сортируем по версии
        migrations.sort(key=lambda m: m.version)
        return migrations

    def _extract_sql_section(self, content: str, section_name: str) -> str:
        """Извлекает SQL код из указанной секции."""
        lines = content.split('\n')
        in_section = False
        sql_lines = []

        for line in lines:
            if f"-- {section_name}" in line:
                in_section = True
                continue
            if in_section and line.strip().startswith('--') and 'migration' in line.lower():
                break
            if in_section and line.strip() and not line.strip().startswith('--'):
                sql_lines.append(line)

        return '\n'.join(sql_lines).strip()

# Пример использования генератора миграций
if __name__ == "__main__":
    # Пример создания менеджера миграций
    manager = MigrationManager(
        db_url="postgresql://user:password@localhost:5432/dbname",
        migrations_dir="migrations"
    )

    # Генерация новой миграции
    migration_file = manager.generate_migration_template(
        name="CreateUsersTable",
        description="Создание таблицы пользователей"
    )

    print(f"Создан файл миграции: {migration_file}")
