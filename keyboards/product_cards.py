"""Module keyboards.product_cards

This module contains functions for creating keyboard layouts for product cards.

"""
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_product_card_keyboard(product_id: int):
    """
    Создает клавиатуру для карточки товара
    Args:
        product_id: ID товара для callback данных
    Returns:
        InlineKeyboardBuilder с кнопками действий
    """
    builder = InlineKeyboardBuilder()

    # Основные действия с товаром
    builder.button(
        text="🛒 В корзину",
        callback_data=f"add_to_cart_{product_id}"
    )
    builder.button(
        text="📰 Описание",
        callback_data=f"description_{product_id}"
    )
    builder.button(
        text="⚡ Быстрый заказ",
        callback_data=f"quick_order_{product_id}"
    )
    #
    # Сетка: первые две кнопки в ряд, третья отдельно
    builder.adjust(2, 1)

    return builder


def create_product_details_keyboard(product_id: int):
    """
    Создает расширенную клавиатуру для детального просмотра товара
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Характеристики",
        callback_data=f"product_specs_{product_id}"
    )
    builder.button(
        text="📸 Еще фото",
        callback_data=f"more_photos_{product_id}"
    )
    builder.button(
        text="🛒 В корзину",
        callback_data=f"add_to_cart_{product_id}"
    )
    builder.button(
        text="📞 Консультация",
        callback_data=f"consult_{product_id}"
    )

    builder.adjust(2, 1, 1)
    return builder