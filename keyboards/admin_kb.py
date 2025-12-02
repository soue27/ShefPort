from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import get_all_categories, session, count_model_records
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
                InlineKeyboardButton(text=f"{count_order} - {text_order.capitalize()} для сбора", callback_data="done_order"),
                InlineKeyboardButton(text=f"{count_order_issued} - {text_order.capitalize()} для выдачи" , callback_data="issued_order"),
                InlineKeyboardButton(text=f"{count2} - {text2.capitalize()}", callback_data="check_questions"),
                InlineKeyboardButton(text="Рассылка", callback_data="mailing"))
    builder.adjust(2)

    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def check_questions():
    """Клавиатура для проверки сообщений"""
    count2 = count_model_records(session, Question, filters=[Question.is_answered == False])
    text = plural_form(count2, ("новое", "новых", "новых"))
    text2 = plural_form(count2, ("сообщение", "сообщения", "сообщений"))
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Все сообщения", callback_data="all_questions"),
                InlineKeyboardButton(text=f"{count2} - {text.capitalize()} {text2}", callback_data="new_questions"))
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
                InlineKeyboardButton(text=f"Изменить", callback_data="mailing_cancel"))
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
        builder.button(text=f"{text} №{entity.id}", callback_data=f"{call}_{entity.id}")
        builder.adjust(1)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_admin_confirmentity_kb(entity_id, model):
    builder = InlineKeyboardBuilder()
    if model == "Cart":
        text = "✅ Готов к выдаче"
        call = "Cart"
    else:
        text = "✅  Произведен заказ"
        call = "Order"
    builder.row(InlineKeyboardButton(text=f"{text} №{entity_id}", callback_data=f"{call}Done_{entity_id}"),
                InlineKeyboardButton(text=f"🔙 Назад", callback_data="Back"))
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)


def get_close_entity(entity_id, model):
    builder = InlineKeyboardBuilder()
    if model == "Cart":
        call = "Cart"
    else:
        call = "Order"
    builder.row(InlineKeyboardButton(text=f"📝 Уведомить клиента", callback_data=f"{call}DoneMessage_{entity_id}"),
                InlineKeyboardButton(text=f"➕ комментарий", callback_data=f"{call}DoneMessage_comm_{entity_id}"),
                InlineKeyboardButton(text=f"🔙 Назад", callback_data="Back"))
    builder.adjust(2)
    return builder.as_markup(one_time_keyboard=True, resize_keyboard=True)