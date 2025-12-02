"""
Category Keyboard Module for Telegram Bot

This module provides functionality to create and manage inline keyboards
for displaying product categories with pagination support. It's designed
to work with the aiogram library and integrates with the database
module to fetch category data.

Key Features:
- Dynamic category listing with pagination
- Navigation controls (Previous/Next)
- Inline keyboard generation for category selection
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import get_all_categories, session


def get_categories_kb(categories: list, page: int = 0) -> InlineKeyboardMarkup:
    """
    Generates an inline keyboard with paginated categories.

    This function creates a grid of category buttons with navigation controls.
    Each category button is created with a callback_data in the format
    'category_<category_id>'. Navigation buttons are added if there are
    multiple pages of categories.

    :param categories: List of category objects to display on the current page
    :type categories: list[Category]
    :param page: Current page number (0-based), defaults to 0
    :type page: int, optional
    :return: Configured InlineKeyboardMarkup with categories and navigation
    :rtype: aiogram.types.InlineKeyboardMarkup
    :note: The function assumes each category object has 'name' and 'id' attributes
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


def get_exit_search_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌Выйти", callback_data="exit_search")
    return builder.as_markup()
