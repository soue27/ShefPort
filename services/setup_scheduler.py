from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.backup_jobs import backup_and_upload
from services.mail_checker import check_mail_and_download
from loguru import logger




async def start_sheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    logger.info("Starting sheduler")
    scheduler.add_job(
        check_mail_and_download,
        args=(bot,),  # Pass the bot instance to the function
        trigger="cron",
        hour=21,
        minute=0
        )
    logger.info("Start logging")
    scheduler.add_job(
        backup_and_upload,
        trigger="cron",
        hour=21,
        minute=10
        )
    scheduler.start()

