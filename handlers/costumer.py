"""
Module handlers.costumer

This module contains handlers for customer interactions in the Telegram bot.
It handles product categories display, product search, and related commands.
"""

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from loguru import logger

from database.db import session, get_all_categories, search_products, save_question, get_all_admin, get_costumer_id

from handlers.product_helpers import start_category_products
from handlers.search_helpers import (
    send_search_results_batch, 
    register_search_handlers,
    search_states,
    SearchState
)
from keyboards.categorieskb import get_categories_kb, get_exit_search_kb, show_in_stock_kb

router = Router(name='costumer')


from sqlalchemy.exc import SQLAlchemyError

def commit_session(session):
    """Коммитим изменения с обработкой ошибок и откатом при исключении."""
    try:
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(f"Ошибка при коммите сессии: {e}")
        raise


class SearchProduct(StatesGroup):
    """
    FSM (Finite State Machine) class for handling product search.
    
    Attributes:
        search_word (State): State for storing the search query input by the user.
    """
    search_word = State()


class SendMessage(StatesGroup):
    user_message = State()


@router.message(F.text == '🐠 Категории товаров')
async def show_categories(message: Message):
    """Handles the 'Categories' button click and displays a list of product categories.
    Args:
        message (Message): The incoming message from the user.
    Returns:
        None: Sends a message with a list of categories to the user.
    """
    await message.answer("Выберите режим показа товаров:", reply_markup=show_in_stock_kb())


@router.callback_query(F.data.startswith('category_'))
async def show_product_bycategory(callback: types.CallbackQuery, state: FSMContext):
    """Handles category selection from the categories keyboard.
    Args:
        callback (CallbackQuery): The callback query containing the selected category ID.
        state
    Returns:
        None: Displays products from the selected category.
    """
    try:
        category_id = int(callback.data.split("_")[1])
    except Exception as e:
        logger.exception(
            f" Ошибка преобразования ай ди категории в 'costumer.show_product_bycategory': {e}"
        )
        return
    my_data = await state.get_data()
    in_stock = my_data['in_stock']
    await start_category_products(callback.message, category_id, session, in_stock=in_stock)
    await callback.answer()


@router.message(F.text == '🔎 Поиск товара')
async def show_search(message: Message, state: FSMContext):
    """Initiates the product search process.
    Args:
        message (Message): The incoming message from the user.
        state (FSMContext): The current state of the conversation.
        Returns:
        None: Prompts the user to enter a search query.
    """
    await message.answer("Введите запрос для поиска товара:")
    logger.info(f"пользователь {message.from_user.id} перешел в стейт SearchProduct.search_word в coctumer.show_search")
    await state.set_state(SearchProduct.search_word)


@router.message(SearchProduct.search_word)
async def get_search(message: Message, state: FSMContext):
    """ Processes the search query and displays matching products.
    Args:
        message (Message): The incoming message containing the search query.
        state (FSMContext): The current state of the conversation.
        Returns:
        None: Displays search results or an appropriate message if no results found.
    """
    search_query = message.text.strip()
    # Выполняем поиск товаров
    try:
        products = search_products(session=session, query=search_query)
        logger.info(
        f"'costumer.get_search: пользователь {message.from_user.id} получил данные 'search_products' "
    )
    except Exception as e:
        logger.exception(
        f" Запрос пользователя {message.from_user.id} в БД 'search_products'"
        f"в 'costumer.get_search' выполнен неуспешно: {e}"
    )
        return
    if not products:
        await message.answer(f"К сожалению, товары по запросу '{search_query}' не найдены. Попробуйте изменить запрос.",
                             reply_markup=get_exit_search_kb())
        await state.set_state(SearchProduct.search_word)
        return
    # Сохраняем состояние поиска
    user_id = message.from_user.id
    search_states[user_id] = SearchState(
        query=search_query,
        products=products
    )
    # Отправляем первую порцию товаров
    await send_search_results_batch(message, products, offset=0)
    await state.clear()

# Регистрируем обработчики поиска
register_search_handlers(router)


@router.message(F.text == '📝 Написать сообщение')
async def send_message(message: Message, state: FSMContext):
    """Обраьотка кнопки Напистаь сообщение, запуск FSM
     :param """
    await message.answer("Введите Ваше сообщение:")
    logger.info(
        f"пользователь {message.from_user.id} перешел в стейт SendMessage.user_message в coctumer.send_message"
    )
    await state.set_state(SendMessage.user_message)


@router.message(SendMessage.user_message)
async def get_message(message: Message, state: FSMContext, bot: Bot):
    """Processes the user's message and saves it to the database.
    Args:
        message (Message): The incoming message from the user.
        state (FSMContext): The current state of the conversation.
        bot
    Returns:
        None: Saves the message to the database and sends a confirmation message to the user.
    """
    try:
        user_id = get_costumer_id(session, message.from_user.id)
        print(user_id)
        save_question(session, user_id, message.from_user.id, message.text)
        logger.info(
        f"'costumer.get_message: пользователь {message.from_user.id} сохранил данные 'save_question' "
        )
        commit_session(session)
    except Exception as e:
        logger.exception(
        f" Запрос пользователя {message.from_user.id} в БД 'save_question'"
        f"в 'costumer.get_message' выполнен неуспешно: {e}"
        )
        return
    await message.answer("Спасибо, за Ваше сообщение. Мы ответим в ближайшее время!")
    try:
        admins = get_all_admin(session)
        logger.info(
        "'costumer.get_message:  получены данные 'get_all_admin' "
        )
    except Exception as e:
        logger.exception(
        f" Запрос  в БД 'get_all_admin'"
        f"в 'costumer.get_message' выполнен неуспешно: {e}"
        )
        return
    for admin in admins:
        await bot.send_message(chat_id=admin, text=f"Получено сообщение от {message.from_user.full_name}: {message.text[:20]}")
    await state.clear()


@router.callback_query(F.data == 'exit_search')
async def exit_search(callback: types.CallbackQuery, state: FSMContext):
    """Обработка команды выхода из поиска"""
    await callback.message.answer("Для повтора поиска нажмите 🔎 Поиск товара")
    await state.clear()


@router.callback_query(F.data.in_(['in_stock', 'show_all']))
async def in_stock_category(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора показа товаров - только из наличия или весь каталог"""
    if callback.data == 'in_stock':
        await state.update_data(in_stock=True)
    else:
        await state.update_data(in_stock=False)
    try:
        categories = get_all_categories(session)
        logger.info(
        "'costumer.in_stock_category:  получены данные 'get_all_categories' "
        )
    except Exception as e:
        logger.exception(
        f" Запрос  в БД 'get_all_categories'"
        f"в 'in_stock_category' выполнен неуспешно: {e}"
        )
        return
    await callback.message.answer(
        text="Выберете категорию товара:",
        reply_markup=get_categories_kb(categories),
        )
    await callback.answer()



# End of handlers/costumer.py

