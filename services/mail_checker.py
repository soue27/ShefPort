import imaplib
import email
import logging
import os


from data.config import MAIL_USER, MAIL_PASS, SENDER_FILTER, READ_DIR, MAIL_HOST
from database.db import session
from handlers.admin import send_file_to_admin
from services.db_updater import load_report, update_products_from_df

# Конфигурация
# MAIL_HOST = "imap.mail.ru"
# MAIL_USER = "your_email@mail.ru"
# MAIL_PASS = "your_app_password"   # пароль приложения Mail.ru
# SENDER_FILTER = "sender@example.com"
# SAVE_DIR = "attachments"

logger = logging.getLogger("mail_checker")

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# SAVE_DIR = os.path.join(BASE_DIR, "..", "data")
SAVE_DIR = os.path.normpath("data")
os.makedirs(SAVE_DIR, exist_ok=True)


async def check_mail_and_download(bot=None):
    """
    Check mail for new messages and process attachments.
    
    Args:
        bot: Optional bot instance to send notifications
    """
    logger.info("Старт проверки почты...")

    try:
        mail = imaplib.IMAP4_SSL(MAIL_HOST)
        mail.login(MAIL_USER, MAIL_PASS)
        mail.select(READ_DIR)
        # Непрочитанные письма от нужного адреса
        status, messages = mail.search(None, f'(FROM "{SENDER_FILTER}")')

        if status != "OK":
            logger.warning("Ошибка поиска писем")
            mail.logout()
            return

        msg_ids = messages[0].split()
        if not msg_ids:
            logger.info("Нет новых писем от отправителя")
            mail.logout()
            return

        for msg_id in msg_ids:
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                logger.warning(f"Ошибка чтения письма {msg_id}")
                continue

            msg = email.message_from_bytes(msg_data[0][1])

            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    print(filename)
                    if filename:
                        filepath = os.path.join(SAVE_DIR, "report.xls")
                        print(filepath)
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        logger.info(f"Скачан файл: {filename}")

            # Удаляем письмо
            mail.store(msg_id, "+FLAGS", "\\Deleted")
            logger.info("Письмо удалено")

        mail.expunge()
        mail.logout()
        logger.info("Проверка почты завершена")

    except Exception as e:
        logger.error(f"Ошибка при работе с почтой: {e}")
    #Обработка файла, загрузка в БД, выборка отсутствующих товаров и отправка админу
    df = load_report()
    count = update_products_from_df(df=df, session=session)
    print(df, df.shape)
    print(count)
    if bot and count > 0:  # Only try to send file if bot instance is provided
        await send_file_to_admin("data/output.xlsx", bot)