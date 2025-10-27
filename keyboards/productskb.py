"""Module keyboards.productskb

This module contains functions for creating keyboard layouts for product navigation.

"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from datadase.db import get_all_categories, session


def get_products_kb(products: list, page: int = 0, items_per_page: int = 8):
    """
    Returns an inline keyboard with products pagination.
    """
    builder = InlineKeyboardBuilder()

    # Вычисляем срез продуктов для текущей страницы
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_products = products[start_idx:end_idx]

    # Добавляем кнопки продуктов текущей страницы
    for product in page_products:
        # Обрезаем длинные названия чтобы избежать переполнения
        button_text = product.name[:30] + "..." if len(product.name) > 30 else product.name
        builder.button(
            text=button_text,
            callback_data=f"product_{product.id}"
        )

    builder.adjust(1)  # Все кнопки в один столбец

    # Навигационные кнопки
    nav_buttons = []
    total_pages = (len(products) + items_per_page - 1) // items_per_page

    # Кнопка "Назад" - показываем если не на первой странице
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"products_page_{page - 1}"
        ))

    # Кнопка "Вперед" - показываем если есть еще продукты
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Вперед",
            callback_data=f"products_page_{page + 1}"
        ))

    # Добавляем навигацию если есть кнопки
    if nav_buttons:
        builder.row(*nav_buttons)

    # Добавляем кнопку возврата в главное меню
    # builder.row(InlineKeyboardButton(
    #     text="🏠 Главное меню",
    #     callback_data="main_menu"
    # ))

    return builder.as_markup()
