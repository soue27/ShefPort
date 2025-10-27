"""Module keyboards.startkb

This module contains functions for creating keyboard layouts for the start menu.

"""
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton


def startkb():
    """
    Create an inline keyboard with two buttons: "Subscribe" and "Unsubscribe"
    which can be used to manage news subscriptions.

    Returns:
        InlineKeyboardMarkup: an inline keyboard markup with two buttons.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=" ✅Подписаться", callback_data="subscribe"),
                InlineKeyboardButton(text="❌Отписаться", callback_data="unsubscribe"))
    return builder.as_markup(one_time_keyboard=True)