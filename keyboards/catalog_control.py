from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_control_keyboard(category_id: int, current_offset: int, total_products: int, batch_size: int = 5):
    """
    Создает клавиатуру управления просмотром товаров
    Args:
        category_id: ID текущей категории
        current_offset: текущая позиция в списке товаров
        total_products: общее количество товаров
        batch_size: размер порции товаров
    Returns:
        InlineKeyboardBuilder с кнопками управления
    """
    builder = InlineKeyboardBuilder()
    has_more_products = current_offset + batch_size < total_products

    # Кнопки навигации
    if has_more_products:
        # Основное продолжение
        builder.button(
            text=f"➡️ Следующие {batch_size} товаров",
            callback_data=f"catalog_continue_{category_id}_{current_offset + batch_size}"
        )

        # Дополнительные опции
        builder.button(
            text="⏸️ Сделать паузу",
            callback_data=f"catalog_pause_{category_id}_{current_offset}"
        )

        # Быстрая навигация для больших каталогов
        if total_products > 20:
            builder.button(
                text="🚀 Пропустить 20 товаров",
                callback_data=f"catalog_skip_{category_id}_{current_offset + 20}"
            )
    else:
        # Все товары просмотрены
        builder.button(
            text="🎉 Просмотр завершен",
            callback_data="catalog_complete"
        )

    # Общие действия
    builder.button(
        text="📂 Сменить категорию",
        callback_data="catalog_change_category"
    )

    builder.button(
        text="🛒 Перейти в корзину",
        callback_data="cart_show"
    )

    builder.button(
        text="❌ Закрыть каталог",
        callback_data="catalog_close"
    )

    # Адаптивная сетка кнопок
    if has_more_products and total_products > 20:
        builder.adjust(1, 1, 2, 1)  # 1, 1, 2, 1 кнопки в рядах
    else:
        builder.adjust(1, 2, 1)

    return builder


def create_pause_keyboard(category_id: int, current_offset: int):
    """
    Создает клавиатуру для режима паузы
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="▶️ Продолжить просмотр",
        callback_data=f"catalog_continue_{category_id}_{current_offset}"
    )
    builder.button(
        text="📂 Выбрать другую категорию",
        callback_data="catalog_change_category"
    )
    builder.button(
        text="❌ Завершить просмотр",
        callback_data="catalog_close"
    )

    builder.adjust(1, 2)
    return builder