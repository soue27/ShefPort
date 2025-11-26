"""
Main keyboard module for the Telegram bot.

This module provides the main keyboard layout and related functionality
for the bot's main menu interface. It includes the primary navigation
options that users can interact with.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_kb() -> ReplyKeyboardMarkup:
    """
    Creates and returns the main keyboard layout for the bot.

    The keyboard includes the following buttons:
    - 🐠 Категории товаров (Product categories)
    - 🔎 Поиск товара (Product search)
    - 🛒 Моя корзина (My cart)
    - 📝 Написать сообщение (Write a message)
    - Заказать товар (Order product)
    - 📰 Новости (News)

    :return: Configured ReplyKeyboardMarkup instance
    :rtype: aiogram.types.ReplyKeyboardMarkup
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🐠 Категории товаров"), KeyboardButton(text="🔎 Поиск товара")],
            [KeyboardButton(text="🛒 Моя корзина"), KeyboardButton(text="📝 Написать сообщение")],
            [KeyboardButton(text="🛍  Мои заказы"), KeyboardButton(text="📰 Новости")]
        ],
        resize_keyboard=True,  # Кнопки подстраиваются под размер
        one_time_keyboard=False,  # Клавиатура не скрывается после нажатия
        input_field_placeholder="Выберите действие..."  # Подсказка в поле ввода
    )
    return keyboard