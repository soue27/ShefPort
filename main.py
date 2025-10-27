import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import logging


from data.config import BOT_TOKEN, DB_URL, ECHO
from datadase.db import session
from datadase.loadfromparser import load_data_from_json, import_data_to_database
from datadase.models import Base, Product, Category
from handlers import user_start, costumer, products, catalog


async def main():
    """
    Main function of the bot.
    This function creates a bot instance, sets up a dispatcher and starts polling.
    """
    # tables_to_check = [Product, Category]
    # lets_go = 0
    # for table in tables_to_check:
    #     count = session.query(table).count()
    #     print(f"Table {table.__name__} has {count} rows")
    #     if count == 0:
    #         lets_go += 1
    # if lets_go == 2:
    #     data = load_data_from_json('chefport_catalog_20251025_221204.json')
    #     import_data_to_database(session, data)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(user_start.router)
    dp.include_router(costumer.router)
    dp.include_router(products.router)
    dp.include_router(catalog.router)
    logger.info("Бот запущен")
    print(DB_URL)
    print(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())