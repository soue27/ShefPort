from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

from data.config import DB_BACKUP_DIR
from services.backup_db import PostrgresBackup
from services.yandex_db import YandexDiskBackup

router = Router(name='admin_recovery')


@router.callback_query(F.data == "recovery_latest")
async def recovery_latest(callback: CallbackQuery, ya: YandexDiskBackup, pg: PostrgresBackup):
    """обработка нажатия кнопки восстановления последнего бэкапа"""
    latest = ya.get_latest_backup()
    backup_file = ya.download_backup(latest, DB_BACKUP_DIR)
    pg.restore_data_backup(backup_file)
    logger.info(f"{callback.from_user.id} восстановил последний бэкап {latest}")
    await callback.message.answer(f"Восстановлен последний бэкап {latest}")
