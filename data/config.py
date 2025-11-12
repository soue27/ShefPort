from dotenv import load_dotenv
import os


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DB_URL')
ECHO = os.getenv('ECHO', 'False').lower() in ('true', '1', 't')

MAIL_HOST = os.getenv('MAIL_HOST')
MAIL_USER = os.getenv('MAIL_USER')
MAIL_PASS = os.getenv('MAIL_PASS')
SENDER_FILTER = os.getenv('SENDER_FILTER')
READ_DIR = os.getenv('READ_DIR')
SUPERADMIN_ID = os.getenv('SUPERADMIN_ID')

