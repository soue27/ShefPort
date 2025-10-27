"""
Module handlers.costumer

This module contains handlers for costumer interactions.

"""
import asyncio

from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.orm import Session

from datadase.db import (session, save_costumer, get_random_photo, get_all_categories,
                         get_products_by_category)

from loguru import logger

from handlers.product_helpers import start_category_products
from keyboards.catalog_control import create_control_keyboard
from keyboards.categorieskb import get_categories_kb
from keyboards.product_cards import create_product_card_keyboard
from keyboards.productskb import get_products_kb

router = Router(name='costumer')


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