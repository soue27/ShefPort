"""Класс для сохранения базы данных на яндекс диске"""

from datetime import datetime, timezone
from pathlib import Path
from yadisk import YaDisk
from loguru import logger

from services.backup_db import PostrgresBackup


class YandexDiskBackup:
    """Класс для загрузки бэкапа на Яндекс диск"""
    def __init__(self, auth_token, remote_folder):
        self.y = YaDisk(token=auth_token)
        self.remote_folder = f"app:/{remote_folder.strip('/')}"

        if not self.y.exists(self.remote_folder):
            self.y.makedirs(self.remote_folder)

    def upload_backup(self, local_path: Path):
        """Загрузка файла на Яндекс.Диск"""
        try:
            remote_path = f"{self.remote_folder}/{local_path.name}"
            self.y.upload(str(local_path), remote_path, overwrite=True)
            logger.info(f"Uploaded backup: {remote_path}")
            return remote_path
        except Exception as e:
            logger.error(f"Failed to upload backup: {e}")


    def clean_old_backups(self, days: int=7):
        """Удаление старых резервных копий"""
        files = list(self.y.listdir(self.remote_folder))
        now = datetime.now(timezone.utc)

        for f in files: #Перебор всех файлов с датой старше 7 дней от сегодня
            mod_time = f.modified
            if mod_time.tzinfo is None: # --- FIX: если дата naive → делаем её UTC-aware ---
                mod_time = mod_time.replace(tzinfo=timezone.utc)
            age_days = (now - mod_time).days
            if age_days >= days:
                path_to_delete = f"{self.remote_folder}/{f.name}"
                try:
                    self.y.remove(path_to_delete)
                    logger.info(f"Deleted old backup: {path_to_delete}")
                except Exception as e:
                    logger.error(f"Failed to delete old backup {path_to_delete}: {e}")


class BackupManager:
    """Класс для запуска менеджера создание бэкапа и сохранения на Яндекс диск"""
    def __init__(self, pg_backup: PostrgresBackup, ya_backup: YandexDiskBackup):
        self.pg_backup = pg_backup
        self.ya_backup = ya_backup

    def run(self):
        """Запуск менеджера"""
        backup_file = self.pg_backup.create_backup()
        remote_path = self.ya_backup.upload_backup(backup_file)
        try: #Удаление файла бекапа с диска
            Path.unlink(backup_file)
            logger.info(f"Deleted backup file: {backup_file}")
        except Exception as e:
            logger.exception(f"Failed to delete backup file {backup_file}: {e}")
        self.ya_backup.clean_old_backups(days=7)




