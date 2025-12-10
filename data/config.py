from dotenv import load_dotenv
import os


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DB_URL')
DB_BACKUP_DIR = os.getenv('DB_BACKUP_DIR')

DB_NAME = os.getenv('POSTGRES_DB')
DB_HOST = os.getenv('POSTGRES_HOST')
DB_PORT = os.getenv('POSTGRES_PORT')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD =  os.getenv('POSTGRES_PASSWORD')
YANDEX_TOKEN = os.getenv('YANDEX_TOKEN')
REMOTE_FOLDER = os.getenv('REMOTE_FOLDER')

ECHO = os.getenv('ECHO', 'False').lower() in ('true', '1', 't')

MAIL_HOST = os.getenv('MAIL_HOST')
MAIL_USER = os.getenv('MAIL_USER')
MAIL_PASS = os.getenv('MAIL_PASS')
SENDER_FILTER = os.getenv('SENDER_FILTER')
READ_DIR = os.getenv('READ_DIR')
SUPERADMIN_ID = os.getenv('SUPERADMIN_ID')

