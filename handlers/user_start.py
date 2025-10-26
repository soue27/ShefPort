"""
Модуль для обработки команд /start и callback запросов для подписки/отписки от новостей.

Обработка команд /start:
    - Ответ на команду /start c приветствием и предложением на получение уведомлений.
    - Отправляет сообщение c кнопками "Подписаться" и "Отписаться".

Обработка callback запросов:
    - Обработка callback запросов с данными "subscribe" и "unsubscribe" для подписки/отписки от новостей.
    - Изменяет значение поля "news" в модели Costumer на True или False в зависимости от данных callback запроса.

"""
""""""

from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart

from datadase.db import session, save_costumer

from loguru import logger

from keyboards.startkb import startkb

router = Router(name='user_start')

@router.message(CommandStart())
async def user_start(message: Message):
    """
    Обработка команды /start:
        - Ответ на команду /start c приветствием и предложением на получение уведомлений.
        - Отправляет сообщение c кнопками "Подписаться" и "Отписаться".
    """
    await message.answer("Привет! Я бот ShefPort. Согласны ли вы на получение уведомлений?", reply_markup=startkb())
    logger.info(f"User {message.from_user.id} started bot {message.from_user.full_name}")


@router.callback_query(F.data.in_(['subscribe', 'unsubscribe']))
async def set_news(callback: types.CallbackQuery):
    """
    Обработка callback запросов с данными "subscribe" и "unsubscribe" для подписки/отписки от новостей:
        - Изменяет значение поля "news" в модели Costumer на True или False в зависимости от данных callback запроса.
    """
    if callback.data == 'subscribe':
        save_costumer(session, callback, news=True)
    elif callback.data == 'unsubscribe':
        save_costumer(session, callback, news=False)
    await callback.message.edit_text(
        "Спасибо, что Вы с нами!!!")
    await callback.answer()




