"""
Module handlers.costumer

This module contains handlers for customer interactions in the Telegram bot.
It handles product categories display, product search, and related commands.
"""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from datadase.db import session, get_all_categories, search_products

from handlers.product_helpers import start_category_products
from handlers.search_helpers import (
    send_search_results_batch, 
    register_search_handlers,
    search_states,
    SearchState
)
from keyboards.categorieskb import get_categories_kb

router = Router(name='costumer')

class SearchProduct(StatesGroup):
    """
    FSM (Finite State Machine) class for handling product search.
    
    Attributes:
        search_word (State): State for storing the search query input by the user.
    """
    search_word = State()


@router.message(F.text == '🐠 Категории товаров')
async def show_categories(message: Message):
    """
    Handles the 'Categories' button click and displays a list of product categories.
    
    Args:
        message (Message): The incoming message from the user.
        
    Returns:
        None: Sends a message with a list of categories to the user.
    """
    categories = get_all_categories(session)
    await message.answer(text="Выберете категорию товара:", reply_markup=get_categories_kb(categories))


@router.callback_query(F.data.startswith('category_'))
async def show_product_bycategory(callback: types.CallbackQuery):
    """
    Handles category selection from the categories keyboard.
    
    Args:
        callback (CallbackQuery): The callback query containing the selected category ID.
        
    Returns:
        None: Displays products from the selected category.
    """
    category_id = int(callback.data.split("_")[1])
    await start_category_products(callback.message, category_id, session)
    await callback.answer()


@router.message(F.text == '🔎 Поиск товара')
async def show_search(message: Message, state: FSMContext):
    """
    Initiates the product search process.
    
    Args:
        message (Message): The incoming message from the user.
        state (FSMContext): The current state of the conversation.
        
    Returns:
        None: Prompts the user to enter a search query.
    """
    await message.answer("Введите запрос для поиска товара:")
    await state.set_state(SearchProduct.search_word)


@router.message(SearchProduct.search_word)
async def get_search(message: Message, state: FSMContext):
    """
    Processes the search query and displays matching products.
    
    Args:
        message (Message): The incoming message containing the search query.
        state (FSMContext): The current state of the conversation.
        
    Returns:
        None: Displays search results or an appropriate message if no results found.
    """
    search_query = message.text.strip()
    # Выполняем поиск товаров
    products = search_products(session=session, query=search_query)
    
    if not products:
        await message.answer(f"К сожалению, товары по запросу '{search_query}' не найдены. Попробуйте изменить запрос.")
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
