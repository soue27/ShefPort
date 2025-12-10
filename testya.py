from yadisk import YaDisk

from data.config import YANDEX_TOKEN

y = YaDisk(token=YANDEX_TOKEN)
print(y)
print(YANDEX_TOKEN, type(YANDEX_TOKEN))
info = y.get_disk_info()
print(info)

try:
    y.disk().get()  # проверяем доступ
    print("Токен рабочий")
except Exception as e:
    print("Ошибка токена:", e)

print(y.disk().get()["system_folders"])
#https://oauth.yandex.ru/authorize?response_type=token&client_id=bf1957257a9e413d8cc038e052250658&force_confirm=yes
