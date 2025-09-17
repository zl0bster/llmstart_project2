#!/usr/bin/env python3
"""
Скрипт для восстановления базы данных OTK Assistant из бэкапа.
Поддерживает SQLite и PostgreSQL.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Optional

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def restore_sqlite_backup(backup_path: Path) -> None:
    """Восстановление SQLite базы данных из бэкапа."""
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    
    # Создаем резервную копию текущей базы данных
    if db_path.exists():
        backup_current = db_path.with_suffix(f".backup_{db_path.suffix}")
        shutil.copy2(db_path, backup_current)
        print(f"📋 Создана резервная копия текущей БД: {backup_current}")
    
    # Восстанавливаем из бэкапа
    shutil.copy2(backup_path, db_path)
    print(f"✅ SQLite база данных восстановлена из: {backup_path}")
    print(f"📁 Восстановлена в: {db_path}")


def restore_postgres_backup(backup_path: Path) -> None:
    """Восстановление PostgreSQL базы данных из бэкапа."""
    # Парсим URL базы данных
    db_url = settings.database_url
    if not db_url.startswith("postgresql://"):
        raise ValueError("Неверный URL PostgreSQL базы данных")
    
    # Извлекаем параметры подключения
    url_parts = db_url.replace("postgresql://", "").split("/")
    if len(url_parts) != 2:
        raise ValueError("Неверный формат URL базы данных")
    
    auth_host, database = url_parts
    if "@" in auth_host:
        auth, host_port = auth_host.split("@")
        if ":" in auth:
            user, password = auth.split(":")
        else:
            user, password = auth, ""
    else:
        user, password = auth_host, ""
        host_port = "localhost:5432"
    
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host, port = host_port, "5432"
    
    # Создаем резервную копию текущей базы данных
    backup_current_name = f"{database}_backup.sql"
    backup_current_path = backup_path.parent / backup_current_name
    
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    
    # Создаем бэкап текущей БД
    dump_cmd = [
        "pg_dump",
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", database,
        "-f", str(backup_current_path),
        "--verbose"
    ]
    
    try:
        subprocess.run(dump_cmd, env=env, check=True)
        print(f"📋 Создана резервная копия текущей БД: {backup_current_path}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Не удалось создать резервную копию текущей БД: {e}")
        print("Продолжаем восстановление...")
    
    # Восстанавливаем из бэкапа
    restore_cmd = [
        "psql",
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", database,
        "-f", str(backup_path),
        "--verbose"
    ]
    
    try:
        subprocess.run(restore_cmd, env=env, check=True)
        print(f"✅ PostgreSQL база данных восстановлена из: {backup_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка восстановления PostgreSQL базы данных: {e}")
        raise
    except FileNotFoundError:
        raise RuntimeError("psql не найден. Установите PostgreSQL client tools.")


def extract_archive(archive_path: Path) -> Path:
    """Извлечение архива бэкапа."""
    if not archive_path.suffix == ".gz" and not archive_path.suffix == ".tar.gz":
        return archive_path
    
    # Создаем временную директорию
    temp_dir = archive_path.parent / "temp_restore"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Извлекаем архив
        shutil.unpack_archive(archive_path, temp_dir)
        
        # Ищем файл базы данных
        db_files = list(temp_dir.rglob("*.db")) + list(temp_dir.rglob("*.sql"))
        if not db_files:
            raise FileNotFoundError("Файл базы данных не найден в архиве")
        
        if len(db_files) > 1:
            print(f"⚠️ Найдено несколько файлов БД: {[f.name for f in db_files]}")
            print("Используется первый найденный файл")
        
        extracted_file = db_files[0]
        print(f"📦 Извлечен файл из архива: {extracted_file}")
        return extracted_file
        
    except Exception as e:
        # Очищаем временную директорию при ошибке
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(description="Восстановление базы данных OTK Assistant из бэкапа")
    parser.add_argument(
        "backup_path",
        type=str,
        help="Путь к файлу бэкапа"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Принудительное восстановление без подтверждения"
    )
    
    args = parser.parse_args()
    
    try:
        backup_path = Path(args.backup_path)
        
        if not backup_path.exists():
            print(f"❌ Файл бэкапа не найден: {backup_path}")
            sys.exit(1)
        
        print(f"🔄 Восстановление базы данных из бэкапа...")
        print(f"📁 Файл бэкапа: {backup_path.absolute()}")
        print(f"🔗 URL базы данных: {settings.database_url}")
        
        # Подтверждение от пользователя
        if not args.force:
            response = input("⚠️ Это действие перезапишет текущую базу данных. Продолжить? (y/N): ")
            if response.lower() not in ['y', 'yes', 'да']:
                print("❌ Восстановление отменено")
                sys.exit(0)
        
        # Извлекаем архив если нужно
        if backup_path.suffix in ['.gz', '.tar.gz']:
            backup_path = extract_archive(backup_path)
        
        # Определяем тип базы данных и восстанавливаем
        if settings.database_url.startswith("sqlite://"):
            restore_sqlite_backup(backup_path)
        elif settings.database_url.startswith("postgresql://"):
            restore_postgres_backup(backup_path)
        else:
            raise ValueError(f"Неподдерживаемый тип базы данных: {settings.database_url}")
        
        print(f"🎉 База данных успешно восстановлена!")
        print("💡 Рекомендуется перезапустить приложение для применения изменений")
        
    except Exception as e:
        print(f"❌ Ошибка восстановления базы данных: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
