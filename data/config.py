from dotenv import load_dotenv
import os


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DB_URL')
ECHO = os.getenv('ECHO', 'False').lower() in ('true', '1', 't')