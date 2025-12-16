"""Модуль для создания резервных копий базы данных и восстановления"""

import os
from datetime import datetime
from pathlib import Path
from loguru import logger

import subprocess


class PostrgresBackup:
    """Класс для создния бэкапа базы данных"""
    def __init__(self, db_name, user, host, port, backup_dir, pg_password, full: bool = False):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = user
        self.pg_password = pg_password
        self.full = full
        self.backup_dir = Path(backup_dir)

        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self):
        """Создание .sql файла с дампом PostgreSQL"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        suffix = "full" if self.full else "data"
        filename = f"{self.db_name}_{suffix}_{date_str}.sql"

        filepath = self.backup_dir / filename

        env = os.environ.copy()
        if self.pg_password:
            env['PGPASSWORD'] = self.pg_password

        cmd = [
            "pg_dump",
            "-U", self.user,
            "-h", self.host,
            "-p", str(self.port),
            "-d", self.db_name,
            "-f", str(filepath)
        ]
        if self.full:
            cmd.append("-Fc")
        else:
            cmd.append("--data-only")
            cmd.append("--inserts")

        try:
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"{'full' if self.full else 'data-only'} Backup created successfully: {filepath}")
        except Exception as e:
            logger.exception(f"Failed to create backup: {e}")
            raise e
        print(filepath)
        return filepath

    def restore_full_backup(self, backup_path: str):
        """Восстановление базы данных из полного бэкапа"""
        env = os.environ.copy()
        if not Path(backup_path).exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        logger.info(f"Starting Restore backup from dump: {backup_path}")
        if self.pg_password is not None:
            env['PGPASSWORD'] = self.pg_password

        # --- загружаем данные ---
        cmd = [
            "psql",
            "-U", self.user,
            "-h", self.host,
            "-p", str(self.port),
            "-d", self.db_name,
            "-f", backup_path,
        ]
        logger.info(f"Running command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"Backup restored successfully")
        except Exception as e:
            logger.exception(f"Failed to restore backup: {e}")
            raise e

    def _truncate_all_tables(self):
        """
        Безопасно очищает все таблицы в public перед restore.
        - Завершает только idle in transaction, кроме текущего процесса
        - Использует один TRUNCATE statement через string_agg
        - Логирует прогресс
        """
        logger.info("Dropping all tables before restore...")

        sql = """
    -- отключаем проверки FK
    SET session_replication_role = replica;

    DO $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ';';
        END LOOP;
    END $$;

    -- включаем проверки FK обратно
    SET session_replication_role = DEFAULT;
    """
        print(self.user)

        cmd = [
            "psql",
            "-U", self.user,  # пользователь-владелец схемы
            "-h", self.host,
            "-p", str(self.port),
            "-d", self.db_name,
            "-c", sql
        ]

        env = os.environ.copy()
        if self.pg_password:
            env["PGPASSWORD"] = self.pg_password


        try:
            subprocess.run(cmd, check=True, env=env, text=True)
            logger.info("All tables dropped successfully.")
        except Exception as e:
            logger.exception(f"Failed to drop tables: {e}")
            raise

    def restore_data_backup(self, backup_path: str):
        """Восстановление базы данных из бэкапа"""
        env = os.environ.copy()
        if not Path(backup_path).exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        logger.info(f"Starting Restore backup from dump: {backup_path}")
        if self.pg_password:
            env['PGPASSWORD'] = self.pg_password

            # --- очищаем таблицы ---
        self._truncate_all_tables()

        # --- загружаем данные ---
        cmd = [
            "psql",
            "-U", self.user,
            "-h", self.host,
            "-p", str(self.port),
            "-d", self.db_name,
            "-f", backup_path,
        ]
        logger.info(f"Running command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"Backup restored successfully")
        except Exception as e:
            logger.exception(f"Failed to restore backup: {e}")
            raise e