import imaplib
import email
import logging
import os
from data.config import MAIL_USER, MAIL_PASS, SENDER_FILTER, SAVE_DIR, MAIL_HOST

# Конфигурация
# MAIL_HOST = "imap.mail.ru"
# MAIL_USER = "your_email@mail.ru"
# MAIL_PASS = "your_app_password"   # пароль приложения Mail.ru
# SENDER_FILTER = "sender@example.com"
# SAVE_DIR = "attachments"

logger = logging.getLogger("mail_checker")

os.makedirs(SAVE_DIR, exist_ok=True)


def check_mail_and_download():
    logger.info("Старт проверки почты...")

    try:
        mail = imaplib.IMAP4_SSL(MAIL_HOST)
        mail.login(MAIL_USER, MAIL_PASS)
        mail.select("INBOX")

        # Непрочитанные письма от нужного адреса
        status, messages = mail.search(None, f'(UNSEEN FROM "{SENDER_FILTER}")')

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
                    if filename:
                        filepath = os.path.join(SAVE_DIR, "report.xls")
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
