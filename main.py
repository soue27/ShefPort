import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from aiogram.fsm.storage.memory import MemoryStorage

from data.config import BOT_TOKEN
from handlers import user_start, costumer, products, catalog, admin, orders, carts
from services.setup_log import setup_logging

from services.setup_scheduler import start_sheduler




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
    dp.include_router(user_start.router)

    dp.include_router(products.router)
    dp.include_router(catalog.router)
    dp.include_router(admin.router)
    dp.include_router(carts.router)
    dp.include_router(orders.router)
    dp.include_router(costumer.router)
    sheduler = await start_sheduler(bot)
    logger.info("Бот запущен")
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())