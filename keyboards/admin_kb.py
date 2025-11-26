from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import get_all_categories, session, count_model_records
from database.models import Question, Cart
from services.search import plural_form


def main_kb() -> InlineKeyboardMarkup:
    """Клавиатура для администратора"""
    count = count_model_records(session, Cart, filters=[Cart.is_done == False]) # подсчет количества Незавершенных заказы
    text = plural_form(count, ("заказ", "заказа", "заказов"))
    count2 = count_model_records(session, Question, filters=[Question.is_answered == False]) # подсчет количества сообщений в работе
    text2 = plural_form(count2, ("сообщение", "сообщения", "сообщений"))
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"{count} - {text.capitalize()}", callback_data="check_carts"),
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