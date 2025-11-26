from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_describe_keyboard(product_id: int, order: bool):
    """
    Создает клавиатуру для карточки товара
    Args:
        product_id: ID товара для callback данных
        order: Флаг заказа
    Returns:
        InlineKeyboardBuilder с кнопками действий
    """
    if order:
        text = "⚡ Заказать"
        data = f"add_to_order_{product_id}"
    else:
        text = "🛒 В корзину"
        data = f"add_to_cart_{product_id}"


    builder = InlineKeyboardBuilder()

    # Основные действия с товаром
    builder.button(
        text=text,
        callback_data=data
    )
    builder.button(
        text="❌ Закрыть",
        callback_data="close_describe"
    )
    # Сетка: первые две кнопки в ряд, третья отдельно
    builder.adjust(2, 1)

    return builder
