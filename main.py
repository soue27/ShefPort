import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from data.config import BOT_TOKEN
from handlers import user_start, costumer, products, catalog, admin, orders, carts
from services.mail_checker import check_mail_and_download

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def setup_logging():
    logger.remove()
    # =========================
    # 1) вывод в Консоль
    # =========================
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | {name} | <level>{level}</level> | {message}",
        level="DEBUG",
    )
    # =========================
    # 2) Файл debug.log — все уровни
    # =========================
    logger.add(
        "logs/debug.log",
        rotation="1 week",
        compression="zip",
        level="DEBUG",
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {name} | {level} | {message}",
    )
    # =========================
    # 3) Файл app.log — только ошибки
    # =========================
    logger.add(
        "logs/error.log",
        rotation="1 week",
        compression="zip",
        level="ERROR",
        enqueue=True,
        filter=lambda record: record["level"].no >= 40,
        format="{time:YYYY-MM-DD HH:mm:ss} | {name} | {level} | {message}",
    )

async def main():
    """
    Main function of the bot.
    This function creates a bot instance, sets up a dispatcher and starts polling.
    """
    storage = MemoryStorage()
    setup_logging()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)
    dp.include_router(user_start.router)
    dp.include_router(costumer.router)
    dp.include_router(products.router)
    dp.include_router(catalog.router)
    dp.include_router(admin.router)
    dp.include_router(carts.router)
    dp.include_router(orders.router)
    #Ежедневный запуск опроса почты
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_mail_and_download,
        args=(bot,),  # Pass the bot instance to the function
        trigger="cron",
        hour=21,
        minute=00
    )
    # scheduler.add_job(
    #     check_mail_and_download,
    #     trigger="interval",
    #     minutes=5
    # )
    scheduler.start()
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())