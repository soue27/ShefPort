"""Module keyboards.categorieskb

This module contains functions for creating keyboard layouts for category navigation.

"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from datadase.db import get_all_categories, session


def get_categories_kb(categories: list, page: int = 0):
    """
    Returns an inline keyboard with categories.
    """
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category.name, callback_data=f"category_{category.id}")
    builder.adjust(2)
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"page_{page - 1}"
        ))
    if len(categories) == 6:  # Если есть еще категории
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Вперед",
            callback_data=f"page_{page + 1}"
        ))

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()
