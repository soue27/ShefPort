from yadisk import YaDisk

from data.config import YANDEX_TOKEN, REMOTE_FOLDER
from services.yandex_db import YandexDiskBackup

ya = YandexDiskBackup(YANDEX_TOKEN, REMOTE_FOLDER)

print(ya.get_list_backups())
print(ya.get_latest_backup())


#https://oauth.yandex.ru/authorize?response_type=token&client_id=bf1957257a9e413d8cc038e052250658&force_confirm=yes
