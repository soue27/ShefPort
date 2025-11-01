"""
Клавиатура для главного меню
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_kb():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🐠 Категории товаров"), KeyboardButton(text="🔎 Поиск товара")],
            [KeyboardButton(text="🛒 Моя корзина"), KeyboardButton(text="📝 Написать сообщение")],
            [KeyboardButton(text="Заказать товар"), KeyboardButton(text="📰 Новости")]
        ],
        resize_keyboard=True,  # Кнопки подстраиваются под размер
        one_time_keyboard=False,  # Клавиатура не скрывается после нажатия
        input_field_placeholder="Выберите действие..."  # Подсказка в поле ввода
    )
    return keyboard