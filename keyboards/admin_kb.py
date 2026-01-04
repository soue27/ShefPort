from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import session, count_model_records, get_all_tables_names
from database.models import Question, Cart, Order
from services.search import plural_form


def main_kb() -> InlineKeyboardMarkup:
    """Клавиатура для администратора"""
    count_cart = count_model_records(session, Cart,
                                     filters=[Cart.is_done == True])  # подсчет количества Незавершенных заказы
    count_cart_issued = count_model_records(session, Cart, filters=[Cart.is_issued == True])
    count_order = count_model_records(session, Order, filters=[Order.is_done == True])
    count_order_issued = count_model_records(session, Order, filters=[Order.is_issued == True])
    text_cart = plural_form(count_cart, ("корзина", "корзины", "корзин"))
    text_order = plural_form(count_order, ("заказ", "заказа", "заказов"))
    count2 = count_model_records(session, Question,
                                 filters=[Question.is_answered == False])  # подсчет количества сообщений в работе
    text2 = plural_form(count2, ("сообщение", "сообщения", "сообщений"))
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"{count_cart} - {text_cart.capitalize()} для сбора",
                             callback_data="done_carts"),
        InlineKeyboardButton(text=f"{count_cart_issued} - {text_cart.capitalize()} для выдачи",
                             callback_data="issued_carts"),
        InlineKeyboardButton(text=f"{count_order} - {text_order.capitalize()} для сбора", callback_data="done_orders"),
        InlineKeyboardButton(text=f"{count_order_issued} - {text_order.capitalize()} для выдачи",
                             callback_data="issued_orders"),
        InlineKeyboardButton(text=f"{count2} - {text2.capitalize()}", callback_data="check_questions"),
        InlineKeyboardButton(text="Рассылка", callback_data="mailing"),
        #  InlineKeyboardButton(text="Recovery latest", callback_data="recovery_latest"),
        # InlineKeyboardButton(text="Recovery list", callback_data="recovery_list"),

        # InlineKeyboardButton(text="Просмотр/Изменение товара", callback_data="edit_product"),
        InlineKeyboardButton(text="Upload to Excel", callback_data="upload_xlsx"),
        InlineKeyboardButton(text="Get log file", callback_data="get_log"),
        InlineKeyboardButton(text="Просмотр/Изменение товара", callback_data="view_product"))

    builder.adjust(2)

    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def check_questions(count: int, text: str, text2: str):
    """Клавиатура для проверки сообщений"""

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Все сообщения", callback_data="all_questions"),
                InlineKeyboardButton(text=f"{count} - {text.capitalize()} {text2}", callback_data="new_questions"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_questions(questions: list) -> InlineKeyboardMarkup:
    """Create a keyboard with a list of questions.
    
    Args:
        questions (list): List of question objects to display
        
    Returns:
        InlineKeyboardMarkup: Keyboard with question buttons
    """
    builder = InlineKeyboardBuilder()
    for question in questions:
        builder.button(text=f"№{question.id}-{question.text[:20]}", callback_data=f"question_{question.id}")
    builder.adjust(1)

    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def mailing_kb() -> InlineKeyboardMarkup:
    """Create a keyboard for selecting mailing type.
    
    Returns:
        InlineKeyboardMarkup: Keyboard with mailing type options
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Пост с текстом", callback_data="post_text"),
                InlineKeyboardButton(text=f"Пост с фото/видео", callback_data="post_image"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def confirm_kb() -> InlineKeyboardMarkup:
    """Create a confirmation keyboard for mailing actions.
    
    Returns:
        InlineKeyboardMarkup: Keyboard with confirmation options
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отправить", callback_data="mailing_confirm"),
                InlineKeyboardButton(text="Изменить", callback_data="mailing_cancel"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_entity_kb(entities: list, model: type) -> InlineKeyboardMarkup:
    """Create a keyboard for listing entities (carts or orders).
    
    Args:
        entities (list): List of entity objects to display
        model (type): The model class (Cart or Order) to determine button text
        
    Returns:
        InlineKeyboardMarkup: Keyboard with entity buttons
    """
    builder = InlineKeyboardBuilder()
    if model == Cart:
        text = "Корзина"
        call = "Cart"
    else:
        text = "Заказ"
        call = "Order"
    for entity in entities:
        builder.button(text=f"{text} №{entity.id}", callback_data=f"{call}List_{entity.id}")
        builder.adjust(1)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_admin_confirmentity_kb(entity_id: int, model: str) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard for admin actions on entities.
    
    Args:
        entity_id (int): ID of the entity to confirm
        model (str): Type of entity ("Cart" or "Order")
        
    Returns:
        InlineKeyboardMarkup: Keyboard with confirmation and back buttons
    """
    builder = InlineKeyboardBuilder()
    if model == "Cart":
        text = "✅ Готов к выдаче"
        call = "Cart"
    else:
        text = "✅ Для заказа"
        call = "Order"
    builder.row(InlineKeyboardButton(text=f"{text} №{entity_id}", callback_data=f"{call}Done_{entity_id}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="Back"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_close_entity(entity_id: int, model: str) -> InlineKeyboardMarkup:
    """Create a keyboard for closing an entity with notification options.
    
    Args:
        entity_id (int): ID of the entity to close
        model (str): Type of entity ("Cart" or "Order")
        
    Returns:
        InlineKeyboardMarkup: Keyboard with close options
    """
    builder = InlineKeyboardBuilder()
    if model == "Cart":
        call = "Cart"
    else:
        call = "Order"
    builder.row(InlineKeyboardButton(text="📝 Уведомить клиента", callback_data=f"{call}DoneMessage_{entity_id}"),
                InlineKeyboardButton(text="➕ комментарий", callback_data=f"{call}DoneMessage_comm_{entity_id}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="Back"))
    builder.adjust(2)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_issued_entity(entity_id: int, model: str) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard for marking an order/cart as issued to the client.
    Args:
        entity_id (int): The ID of the cart or order
        model (str): The type of entity ("Cart" or "Order")
    Returns:
        InlineKeyboardMarkup: A keyboard with confirmation and back buttons
    """
    builder = InlineKeyboardBuilder()
    if model == "Cart":
        call = "Cart"
    else:
        call = "Order"
    builder.row(InlineKeyboardButton(text="Заказ выдан клиенту", callback_data=f"{call}Close_{entity_id}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="Back"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_upload_kb():
    """Клавиатура для выбора таблицы для выгрузки"""
    builder = InlineKeyboardBuilder()
    tables = get_all_tables_names()
    for table_name in tables:
        builder.row(InlineKeyboardButton(text=table_name, callback_data=f"export_{table_name}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="export_back"))
    builder.adjust(2)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_product_change_kb(product_id: int, article: int):
    """Клавиатура для выбора вариантов работы с товаром"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"Изменить №{article}", callback_data=f"confirmedit_{product_id}"),
                InlineKeyboardButton(text=f"Удалить №{article}", callback_data=f"delete_{product_id}"))
    builder.adjust(2)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_product_delete_kb(product_id: int):
    """Клавиатура для выбора удаления товара"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"❌ Удалить ", callback_data=f"deleteconfirm_{product_id}"),
                InlineKeyboardButton(text=f"🔙 Отменить ", callback_data=f"deleteback"))
    builder.adjust(2)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_edit_product_kb(product_id: int) -> InlineKeyboardMarkup:
    """Create a keyboard for editing product details.
    
    Args:
        product_id (int): ID of the product to edit
        
    Returns:
        InlineKeyboardMarkup: Keyboard with product editing options
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Название", callback_data=f"edit_name_{product_id}"),
                InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_price_{product_id}"),
                InlineKeyboardButton(text="📦 Остаток", callback_data=f"edit_ostatok_{product_id}"),
                InlineKeyboardButton(text="📏 Ед. измерения", callback_data=f"edit_unit_{product_id}"),
                InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_description_{product_id}"),
                InlineKeyboardButton(text="🖼 Изображение", callback_data=f"edit_image_{product_id}"))
    builder.adjust(2)
    return builder.as_markup(on_time_keyboard=True, resize_keyboard=True)
