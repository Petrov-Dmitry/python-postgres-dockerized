"""
Database migrations package for PostgreSQL
"""
import argparse
import logging
import os
import re

from core.db_manager import DB_URL, DatabaseManager
from dataclasses import dataclass
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class Migration:
    """Класс, представляющий миграцию базы данных."""
    version: int
    up_sql: str
    down_sql: str

class MigrationManager:
    """Менеджер миграций базы данных PostgreSQL."""

    def __init__(self, db_url: str = DB_URL, migrations_dir: str = "migrations"):
        self.db_manager = DatabaseManager(db_url)
        self.migrations_dir = migrations_dir
        self._ensure_migrations_table()
        self._ensure_migrations_dir()

    def _ensure_migrations_dir(self):
        """Создает директорию для миграций, если она не существует."""
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            logger.info(f"Created migrations directory: {self.migrations_dir}")

    def _ensure_migrations_table(self):
        """Создает таблицу для отслеживания миграций, если она не существует."""
        self.db_manager.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def get_current_version(self) -> int:
        """Возвращает текущую версию базы данных."""
        result = self.db_manager.execute("SELECT MAX(version) FROM migrations", fetchone=True)
        return result[0] or 0 if result else 0

    def get_applied_versions(self) -> List[int]:
        """Возвращает список применённых версий миграций."""
        result = self.db_manager.execute("SELECT version FROM migrations ORDER BY version", fetchall=True)
        return [row[0] for row in result]

    def apply_migration(self, migration: Migration):
        """Применяет миграцию."""
        current_version = self.get_current_version()

        if migration.version <= current_version:
            logger.info(f"Migration {migration.version} already applied")
            return False

        with self.db_manager._get_connection() as conn:
            try:
                with self.db_manager._get_cursor(conn) as cursor:
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

    def apply_to_version(self, target_version: int | None, migrations: List[Migration]):
        """Применяет все миграции по порядку до указанной версии."""
        migrations.sort(key=lambda m: m.version)
        current_version = self.get_current_version()

        if not len(migrations):
            print('There are no migrations to apply!')
            return

        if target_version is not None and migrations[-1].version <= target_version:
            print('All migrations have already been applied!')
            return

        for migration in migrations:
            if migration.version > current_version:
                if target_version is None or migration.version <= target_version:
                    self.apply_migration(migration)

    def rollback_migration(self, migration: Migration):
        """Откатывает миграцию."""
        applied_versions = self.get_applied_versions()

        if migration.version not in applied_versions:
            logger.info(f"Migration {migration.version} not applied")
            return False

        with self.db_manager._get_connection() as conn:
            try:
                with self.db_manager._get_cursor(conn) as cursor:
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

    def rollback_to_version(self, target_version: int | None, migrations: List[Migration]):
        """Откатывает миграции до указанной версии."""
        applied_versions = self.get_applied_versions()
        migrations_dict = {m.version: m for m in migrations}

        # Откатываем миграции в обратном порядке
        for version in sorted(applied_versions, reverse=True):
            if version in migrations_dict:
                if target_version is None or version > target_version:
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
        version = datetime.now().strftime("%Y%m%d%H%M%S")

        # Преобразуем имя в snake_case
        snake_case_name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        snake_case_name = re.sub(r'[^a-z0-9_]', '_', snake_case_name)
        snake_case_name = re.sub(r'_+', '_', snake_case_name).strip('_')

        # Создаем имя файла с timestamp для уникальности
        filename = f"{version}_{snake_case_name}.sql"
        filepath = os.path.join(self.migrations_dir, filename)

        # Шаблон миграции
        template = f"""-- Migration: {version}_{snake_case_name}
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

    def show_status(self):
        """Показывает статус всех миграций."""
        applied_versions = self.get_applied_versions()
        migration_files = self.load_migrations_from_dir()

        print("\nMigration Status:")
        print("-" * 80)
        print(f"{'Status':<10} {'Version':<20} {'Title':<50}")
        print("-" * 80)

        for filename in migration_files:
            timestamp = filename.split('_')[0]
            title = ' '.join(filename[15:-3].split('_')).capitalize()
            version = int(datetime.strptime(timestamp, '%Y%m%d%H%M%S').timestamp())

            status = "✓" if version in applied_versions else " "
            print(f"{status:<10} {timestamp:<20} {title:<50}")

        print("-" * 80)

if __name__ == "__main__":
    db_manager = DatabaseManager()
    migrations_manager = MigrationManager(db_manager.db_url)
    migrations = migrations_manager.load_migrations_from_dir()

    parser = argparse.ArgumentParser(description='Database migration management tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Команда create
    create_parser = subparsers.add_parser('create', help='Create a new migration')
    create_parser.add_argument('name', help='Migration name')
    create_parser.add_argument('description', help='Migration description')

    # Команда status
    subparsers.add_parser('status', help='Show migration status')

    # Команда apply
    apply_parser = subparsers.add_parser('apply', help='Apply pending migrations. Use the --to argument to specify the required version.')
    apply_parser.add_argument('--to', type=str, help='Apply migrations up to specific version (YYYYMMDDHHMMSS format)', required=False)

    # Команда rollback
    rollback_parser = subparsers.add_parser('rollback', help='Roll back applied migrations. Use the --to argument to specify the required version.')
    rollback_parser.add_argument('--to', type=str, help='Roll back migrations to specific version (YYYYMMDDHHMMSS format)', required=False)

    args = parser.parse_args()

    if args.command == 'create':
        filepath = migrations_manager.generate_migration_template(args.name, args.description)
        print(f"\nCreated new migration: {os.path.basename(filepath)}")
        print(f"Full path: {filepath}")
        print("\nYou can now edit the file and add your SQL migration commands.")

    elif args.command == 'status':
        migrations_manager.show_status()

    elif args.command == 'apply':
        target_version = None
        if args.to:
            target_version = int(datetime.strptime(args.to, '%Y%m%d%H%M%S').timestamp())
        migrations_manager.apply_to_version(target_version, migrations)
        migrations_manager.get_current_version()

    elif args.command == 'rollback':
        target_version = None
        if args.to:
            target_version = int(datetime.strptime(args.to, '%Y%m%d%H%M%S').timestamp())
        migrations_manager.rollback_to_version(target_version, migrations)
        migrations_manager.get_current_version()

    else:
        parser.print_help()
