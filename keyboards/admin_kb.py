from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import get_all_categories, session, count_model_records, get_all_tables_names
from database.models import Question, Cart, Order
from services.search import plural_form


def main_kb() -> InlineKeyboardMarkup:
    """Клавиатура для администратора"""
    count_cart = count_model_records(session, Cart, filters=[Cart.is_done == True])# подсчет количества Незавершенных заказы
    count_cart_issued = count_model_records(session, Cart, filters=[Cart.is_issued == True])
    count_order = count_model_records(session, Order, filters=[Order.is_done == True])
    count_order_issued = count_model_records(session, Order, filters=[Order.is_issued == True])
    text_cart = plural_form(count_cart, ("корзина", "корзины", "корзин"))
    text_order = plural_form(count_order, ("заказ", "заказа", "заказов"))
    count2 = count_model_records(session, Question, filters=[Question.is_answered == False]) # подсчет количества сообщений в работе
    text2 = plural_form(count2, ("сообщение", "сообщения", "сообщений"))
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"{count_cart} - {text_cart.capitalize()} для сбора", callback_data="done_carts"),
                InlineKeyboardButton(text=f"{count_cart_issued} - {text_cart.capitalize()} для выдачи" , callback_data="issued_carts"),
                InlineKeyboardButton(text=f"{count_order} - {text_order.capitalize()} для сбора", callback_data="done_orders"),
                InlineKeyboardButton(text=f"{count_order_issued} - {text_order.capitalize()} для выдачи" , callback_data="issued_orders"),
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


def check_questions(count: int, text: str, text2:str):
    """Клавиатура для проверки сообщений"""

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Все сообщения", callback_data="all_questions"),
                InlineKeyboardButton(text=f"{count} - {text.capitalize()} {text2}", callback_data="new_questions"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_questions(questions):
    """"""
    builder = InlineKeyboardBuilder()
    for question in questions:
        builder.button(text=f"№{question.id}-{question.text[:20]}", callback_data=f"question_{question.id}")
    builder.adjust(1)

    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def mailing_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Пост с текстом", callback_data="post_text"),
                InlineKeyboardButton(text=f"Пост с фото/видео", callback_data="post_image"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отправить", callback_data="mailing_confirm"),
                InlineKeyboardButton(text="Изменить", callback_data="mailing_cancel"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_entity_kb(entities, model):
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


def get_admin_confirmentity_kb(entity_id, model):
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


def get_close_entity(entity_id, model):
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


def get_issued_entity(entity_id, model):
    builder = InlineKeyboardBuilder()
    if model == "Cart":
        call = "Cart"
    else:
        call = "Order"
    builder.row(InlineKeyboardButton(text="Заказ выдан клиенту", callback_data=f"{call}Close_{entity_id}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="Back"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_upload_kb():
    builder = InlineKeyboardBuilder()
    tables = get_all_tables_names()
    for table_name in tables:
        builder.row(InlineKeyboardButton(text=table_name, callback_data=f"export_{table_name}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="export_back"))
    builder.adjust(2)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_product_change_kb(product_id: int, article: int):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"Изменить №{article}", callback_data=f"change_{product_id}"),
                InlineKeyboardButton(text=f"Удалить №{article}", callback_data=f"delete_{product_id}"))
    builder.adjust(2)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)