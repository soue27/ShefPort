import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from data.config import BOT_TOKEN, DB_URL, ECHO
from datadase.models import Base


async def main():
    """
    Main function of the bot.
    This function creates a bot instance, sets up a dispatcher and starts polling.
    """
    engine = create_engine(DB_URL, echo=ECHO)
    Base.metadata.create_all(engine)
    session = Session(engine)
    connect = engine.connect()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    logger.info("Бот запущен")
    print(DB_URL)
    print(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())