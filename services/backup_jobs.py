from services.backup_db import PostrgresBackup
from services.yandex_db import YandexDiskBackup
from services.yandex_db import BackupManager
from loguru import logger
from pathlib import Path
from data.config import DB_NAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, YANDEX_TOKEN, REMOTE_FOLDER

# async-функция для scheduler
async def backup_and_upload():
    try:
        # --- создаём локальный бэкап ---
        pg_backup = PostrgresBackup(
            db_name="DB_NAME",
            user="DB_USER",
            host="DB_HOST",
            port=5432,
            backup_dir="data/backups",
            pg_password="DB_PASSWORD"
        )
        backup_file: Path = pg_backup.create_backup()  # возвращает Path

        # --- загружаем на Яндекс.Диск ---
        ya_backup = YandexDiskBackup(
            auth_token="YANDEX_TOKEN",
            remote_folder="app:/ShefPortChus/backups"
        )
        manager = BackupManager(
            pg_backup=pg_backup,
            ya_backup=ya_backup
        )
        manager.run()
    except Exception as e:
        logger.error(f"Failed to backup/upload: {e}")
