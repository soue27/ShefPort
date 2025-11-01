"""
Module handlers.costumer

This module contains handlers for costumer interactions.

"""
import asyncio
from email import message_from_string

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.orm import Session

from datadase.db import (session, save_costumer, get_random_photo, get_all_categories,
                         get_products_by_category, search_products)

from loguru import logger

from handlers.product_helpers import start_category_products, send_product_card
from keyboards.catalog_control import create_control_keyboard
from keyboards.categorieskb import get_categories_kb
from keyboards.product_cards import create_product_card_keyboard
from keyboards.productskb import get_products_kb

router = Router(name='costumer')

class SearchProduct(StatesGroup):
    """FSM Класс для обработки поиска товара"""
    search_word = State()


@router.message(F.text == 'Категории товаров')
async def show_categories(message: Message):
    """Обработка кнопки Выбора категории, выводит на экран клавиатуру с категориями"""
    categories = get_all_categories(session)
    await message.answer(text="Выберете категорию товара:", reply_markup=get_categories_kb(categories))


@router.callback_query(F.data.startswith('category_'))
async def show_product_bycategory(callback: types.CallbackQuery):
    """Обработка callback запросов с данными 'category_' для вывода товаров по категории"""
    category_id = int(callback.data.split("_")[1])
    await start_category_products(callback.message, category_id, session)
    await callback.answer()


@router.message(F.text == 'Поиск товара')
async def show_search(message: Message, state: FSMContext):
    """Обработка кнопки Поиск, выводит на экран клавиатуру с категориями"""
    await message.answer(text="Введите наименование товара или запрос:")
    await state.set_state(SearchProduct.search_word)


@router.message(SearchProduct.search_word)
async def get_search(message: Message, state: FSMContext):
    products = search_products(session=session, query=message.text)
    await message.answer(f'Найдено {len(products)} товаров')
    for product in products:
        await send_product_card(message, product)
    await state.clear()



