#!/usr/bin/env python3
"""
Скрипт для создания бэкапа базы данных OTK Assistant.
Поддерживает SQLite и PostgreSQL.
"""

import os
import sys
import shutil
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def create_sqlite_backup(backup_dir: Path) -> str:
    """Создание бэкапа SQLite базы данных."""
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    
    if not db_path.exists():
        raise FileNotFoundError(f"База данных не найдена: {db_path}")
    
    # Создаем имя файла с timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"otk_assistant_backup_{timestamp}.db"
    backup_path = backup_dir / backup_filename
    
    # Копируем файл базы данных
    shutil.copy2(db_path, backup_path)
    
    print(f"✅ SQLite бэкап создан: {backup_path}")
    return str(backup_path)


def create_postgres_backup(backup_dir: Path) -> str:
    """Создание бэкапа PostgreSQL базы данных."""
    # Парсим URL базы данных
    db_url = settings.database_url
    if not db_url.startswith("postgresql://"):
        raise ValueError("Неверный URL PostgreSQL базы данных")
    
    # Извлекаем параметры подключения
    # postgresql://user:password@host:port/database
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
    
    # Создаем имя файла с timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"otk_assistant_backup_{timestamp}.sql"
    backup_path = backup_dir / backup_filename
    
    # Команда pg_dump
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    
    cmd = [
        "pg_dump",
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", database,
        "-f", str(backup_path),
        "--verbose"
    ]
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"✅ PostgreSQL бэкап создан: {backup_path}")
        return str(backup_path)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка создания PostgreSQL бэкапа: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        raise RuntimeError("pg_dump не найден. Установите PostgreSQL client tools.")


def create_archive_backup(backup_path: str, backup_dir: Path) -> str:
    """Создание архива бэкапа."""
    backup_file = Path(backup_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"otk_assistant_backup_{timestamp}.tar.gz"
    archive_path = backup_dir / archive_name
    
    # Создаем архив
    shutil.make_archive(
        str(archive_path).replace(".tar.gz", ""),
        "gztar",
        backup_file.parent,
        backup_file.name
    )
    
    # Удаляем исходный файл
    backup_file.unlink()
    
    print(f"✅ Архив создан: {archive_path}")
    return str(archive_path)


def cleanup_old_backups(backup_dir: Path, keep_days: int = 7) -> None:
    """Удаление старых бэкапов."""
    if not backup_dir.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    removed_count = 0
    
    for backup_file in backup_dir.glob("otk_assistant_backup_*"):
        if backup_file.stat().st_mtime < cutoff_time:
            backup_file.unlink()
            removed_count += 1
            print(f"🗑️ Удален старый бэкап: {backup_file.name}")
    
    if removed_count > 0:
        print(f"✅ Удалено {removed_count} старых бэкапов")
    else:
        print("ℹ️ Старые бэкапы не найдены")


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(description="Создание бэкапа базы данных OTK Assistant")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="downloads",
        help="Директория для сохранения бэкапа (по умолчанию: downloads)"
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Создать архив бэкапа"
    )
    parser.add_argument(
        "--cleanup-days",
        type=int,
        default=7,
        help="Количество дней для хранения бэкапов (по умолчанию: 7)"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Не удалять старые бэкапы"
    )
    
    args = parser.parse_args()
    
    try:
        # Создаем директорию для бэкапов
        backup_dir = Path(args.output_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📦 Создание бэкапа базы данных...")
        print(f"📁 Директория: {backup_dir.absolute()}")
        print(f"🔗 URL базы данных: {settings.database_url}")
        
        # Определяем тип базы данных и создаем бэкап
        if settings.database_url.startswith("sqlite://"):
            backup_path = create_sqlite_backup(backup_dir)
        elif settings.database_url.startswith("postgresql://"):
            backup_path = create_postgres_backup(backup_dir)
        else:
            raise ValueError(f"Неподдерживаемый тип базы данных: {settings.database_url}")
        
        # Создаем архив если нужно
        if args.archive:
            backup_path = create_archive_backup(backup_path, backup_dir)
        
        # Очищаем старые бэкапы
        if not args.no_cleanup:
            cleanup_old_backups(backup_dir, args.cleanup_days)
        
        print(f"🎉 Бэкап успешно создан: {backup_path}")
        
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
