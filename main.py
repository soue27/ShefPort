import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import logging

from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from data.config import BOT_TOKEN
from handlers import user_start, costumer, products, catalog, admin, orders, carts
from services.mail_checker import check_mail_and_download


async def main():
    """
    Main function of the bot.
    This function creates a bot instance, sets up a dispatcher and starts polling.
    """
    storage = MemoryStorage()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
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