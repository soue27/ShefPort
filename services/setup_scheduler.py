from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.db import session
from services.backup_jobs import backup_and_upload
from services.mail_checker import check_mail_and_download
from loguru import logger

from services.statistic import get_statistic_for_week


async def start_sheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    logger.info("Starting sheduler")
    #Проверка почты ежедневно в 21.00
    scheduler.add_job(
        check_mail_and_download,
        args=(bot,),  # Pass the bot instance to the function
        trigger="cron",
        hour=5,
        minute=00
        )
    logger.info("Start logging")
    #Резервное копирование базы данных ежедневно в 06.10
    scheduler.add_job(
        backup_and_upload,
        trigger="cron",
          # Pass the bot instance to the function
        day_of_week="mon",
        hour=1,
        minute=10
        )
    scheduler.add_job(
        get_statistic_for_week,
        trigger="cron",
        args=(session, bot),
        hour=5,
        minute=15
    )
    scheduler.start()
    pass

