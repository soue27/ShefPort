"""Модуль для создания резервных копий базы данных и восстановления"""

import os
from datetime import datetime
from pathlib import Path

import subprocess


class PostrgresBackup:
    """Класс для создния бэкапа базы данных"""
    def __init__(self, db_name, user, host, port, backup_dir, pg_password=None):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = user
        self.pg_password = pg_password
        self.backup_dir = Path(backup_dir)

        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self):
        """Создание .sql файла с дампом PostgreSQL"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{self.db_name}_{date_str}.sql"
        filepath = self.backup_dir / filename

        env = os.environ.copy()
        if self.pg_password:
            env['PGPASSWORD'] = self.pg_password

        cmd = [
            "pg_dump",
            "-h", self.host,
            "-p", str(self.port),
            "-U", self.user,
            "-F", "c",  # формат custom
            "-f", str(filepath),
            self.db_name
        ]
        subprocess.run(cmd, env=env, check=True)
        print(filepath)
        return filepath