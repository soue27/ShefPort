from yadisk import YaDisk

from data.config import (YANDEX_TOKEN, REMOTE_FOLDER,
                         DB_BACKUP_DIR, DB_NAME, DB_USER, DB_HOST,
                         DB_PORT, DB_PORT, DB_PASSWORD)
from services.backup_db import PostrgresBackup
from services.yandex_db import YandexDiskBackup

ya = YandexDiskBackup(YANDEX_TOKEN, REMOTE_FOLDER)

backup_file = ya.get_latest_backup()


print(ya.get_list_backups())
# file_name = backup_file.split("/")[-1]
# # print(backup_file, file_name)
#
#
# local_path = f"{DB_BACKUP_DIR}/{file_name}"
# backup_file = ya.download_backup(backup_file, local_path)
# print(backup_file)
#
#
# dump = PostrgresBackup(
#             db_name=DB_NAME,
#             user=DB_USER,
#             host=DB_HOST,
#             port=DB_PORT,
#             backup_dir=DB_PORT,
#             pg_password=DB_PASSWORD
#         )
#
# dump.restore_data_backup(backup_file)


#https://oauth.yandex.ru/authorize?response_type=token&client_id=bf1957257a9e413d8cc038e052250658&force_confirm=yes
