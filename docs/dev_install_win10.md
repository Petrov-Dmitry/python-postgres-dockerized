# Установка окружения для разработки на Win10

## Для работы понадобятся

* [Git for Windows](https://git-scm.com/download/win) с установками по умолчанию. Лично я изменил только дефолтный редактор с VIM на Nano.
* IDE - лично я использую [Visual Studio Code](https://code.visualstudio.com/download), но на вкус и цвет все фломастеры разные.
* Терминал git-bash
* Установленный на хост-машине Python версии 3.11 или выше

## Установка проекта

* Настраиваем Git hooks командой `git config core.hooksPath .githooks`
* Устанавливаем virtualenv командой `pip install virtualenv`
* Aктивируем виртуальное окружение Python командой `virtualenv env && source env/Scripts/activate`
* При необходимости установки пакетов Python пользуемся командой `pip install {package-name}`

> **&#9888; Важно!**
>
> Не редактируйте файл `requirements.txt` вручную!
>
> Файл `requirements.txt` управляется автоматически через git-hooks:
> * При выполнении коммита файл обновляется автоматически
> * После успешного коммита зависимости устанавливаются автоматически

## Работа с базой данных

### Система миграций

Проект использует систему миграций для управления схемой базы данных PostgreSQL. Файлы миграций сохраняются в директории `migrations` и автоматически применяются при запуске приложения.

#### Управление миграциями

Для управления миграциями используется скрипт `utils/migrations.py`.

#### Доступные команды:

1. Создание новой миграции:
```bash
python -m utils.migrations create "описание миграции"
```
Например:
```bash
python -m utils.migrations create "add user table"
```

2. Просмотр статуса миграций:
```bash
python -m utils.migrations status
```

3. Применение миграций:
```bash
# Применить все ожидающие миграции
python -m utils.migrations apply

# Применить миграции до определенной версии
python -m utils.migrations apply --to 5
```

4. Откат миграций:
```bash
# Откатить последнюю миграцию
python -m utils.migrations rollback

# Откатить до определенной версии
python -m utils.migrations rollback --to 3
```

#### Пример вывода статуса:

```
Migration Status:
--------------------------------------------------------------------------------
Status     Version              Description
--------------------------------------------------------------------------------
✓          1          Initial schema
✓          2          Add user table
✓          3          Add posts table
✓          4          Add categories table
           5          Add email field to user
--------------------------------------------------------------------------------
```

Где:
* ✓ - миграция применена
* пустое место - миграция еще не применена

#### Структура файла миграции

При создании новой миграции в директории `migrations` автоматически генерируется шаблонный файл со следующей структурой:
```python
-- Migration: {next_version:04d}_{snake_case_name}
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
```

Вам нужно только заполнить SQL-команды в `up_sql` (для применения изменений) и `down_sql` (для отката изменений).

> **&#9888; Важно!**
>
> * Никогда не изменяйте существующие миграции после того, как они были вылиты в репозиторий
> * Если нужно исправить ошибку в миграции, создайте новую миграцию с исправлением
