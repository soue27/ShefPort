"""
Модуль для обработки команд /start и callback запросов для подписки/отписки от новостей.

Обработка команд /start:
    - Ответ на команду /start c приветствием и предложением на получение уведомлений.
    - Отправляет сообщение с кнопками "Подписаться" и "Отписаться".

Обработка callback запросов:
    - Обработка callback запросов с данными "subscribe" и "unsubscribe" для подписки/отписки от новостей.
    - Изменяет значение поля "news" в модели Costumer на True или False в зависимости от данных callback запроса.

"""


from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart

from database.db import session, save_costumer, get_random_photo, get_all_categories

from loguru import logger

from keyboards.startkb import startkb
from keyboards.mainkb import get_main_kb

router = Router(name='user_start')


from sqlalchemy.exc import SQLAlchemyError

def commit_session(session):
    """Коммитим изменения с обработкой ошибок и откатом при исключении."""
    try:
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(f"Ошибка при коммите сессии: {e}")
        raise


@router.message(CommandStart())
async def user_start(message: Message):
    """Обработка команды /start:
        - Ответ на команду /start c приветствием и предложением на получение уведомлений.
        - Отправляет сообщение с кнопками "Подписаться" и "Отписаться".
    """
    await message.answer("Привет! Я бот ShefPort. Согласны ли вы на получение уведомлений?", reply_markup=startkb())
    logger.info(f"User {message.from_user.id} started bot {message.from_user.full_name}")


@router.callback_query(F.data.in_(['subscribe', 'unsubscribe']))
async def set_news(callback: types.CallbackQuery):
    """
    Обработка callback запросов с данными "subscribe" и "unsubscribe" для подписки/отписки от новостей:
        - Изменяет значение поля "news" в модели Costumer на True или False в зависимости от данных callback запроса.
        Отправка приветственного сообщения
    """
    if callback.data == 'subscribe':
        try:
            save_costumer(session, callback, news=True)
            commit_session(session)
            logger.info(
                f"'set_news.subscribe':  {callback.from_user.id} получил данные 'save_costumer' "
            )
        except Exception as e:
            logger.exception(
                f" Запрос пользователя {callback.from_user.id} в БД 'save_costumer' "
                f"  в 'set_news.subscribe' выполнен неуспешно: {e}"
            )
            return
    elif callback.data == 'unsubscribe':
        try:
            save_costumer(session, callback, news=False)
            commit_session(session)
            logger.info(
                f"'set_news.unsubscribe':  {callback.from_user.id} получил данные 'save_costumer' "
            )
        except Exception as e:
            logger.exception(
                f" Запрос пользователя {callback.from_user.id} в БД 'save_costumer' "
                f"  в 'set_news.unsubscribe' выполнен неуспешно: {e}"
            )
            return
    try:
        get_all_categories(session=session)
        logger.info(
            f"'set_news:  {callback.from_user.id} получил данные 'get_all_categories' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_all_categories' "
            f"  в 'set_news' выполнен неуспешно: {e}"
        )
        return
    try:
        photo = get_random_photo(session=session)
        logger.info(
            f"'set_news:  {callback.from_user.id} получил данные 'get_random_photo' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_random_photo' "
            f"  в 'set_news' выполнен неуспешно: {e}"
        )
        return
    await callback.message.answer_photo(photo=photo[0], caption=f"Спасибо, что Вы с нами!!! \n на фото <b>'{photo[1]}'</b>", reply_markup=get_main_kb())
    await callback.answer()




