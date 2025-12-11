import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from aiogram.fsm.storage.memory import MemoryStorage

from data.config import (BOT_TOKEN, YANDEX_TOKEN, REMOTE_FOLDER,
                         DB_NAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, DB_BACKUP_DIR)
from handlers import user_start, costumer, products, catalog, admin, orders, carts, admin_recovery
from services.backup_db import PostrgresBackup
from services.setup_log import setup_logging

from services.setup_scheduler import start_sheduler
from services.yandex_db import YandexDiskBackup, BackupManager


async def on_startup(bot):
    await start_sheduler(bot)


async def main():
    """
    Main function of the bot.
    This function creates a bot instance, sets up a dispatcher and starts polling.
    """
    storage = MemoryStorage()
    setup_logging()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher(storage=storage)
    # Добавляем объект YandexDiskBackup в dispatcher
    dp["ya"] = YandexDiskBackup(YANDEX_TOKEN, REMOTE_FOLDER)
    #Добавляем объект PostrgresBackup в dispatcher
    dp["pg"] = PostrgresBackup(DB_NAME, DB_USER, DB_HOST, DB_PORT, DB_BACKUP_DIR, DB_PASSWORD)
    #Добавляем объект BackupManager в dispatcher
    dp["bm"] = BackupManager(dp["pg"], dp["ya"])
    # Подключаем роутеры
    dp.include_router(user_start.router)
    dp.include_router(products.router)
    dp.include_router(catalog.router)
    dp.include_router(admin.router)
    dp.include_router(carts.router)
    dp.include_router(orders.router)
    dp.include_router(costumer.router)
    dp.include_router(admin_recovery.router)
    await start_sheduler(bot)
    logger.info("Бот запущен")
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())