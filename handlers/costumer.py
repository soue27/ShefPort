from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.orm import Session

from datadase.db import (session, save_costumer, get_random_photo, get_all_categories,
                         get_products_by_category)

from loguru import logger
from keyboards.categorieskb import get_categories_kb
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
    products = get_products_by_category(session, category_id)
    if not products:
        await callback.message.answer(text="В этой категории нет товаров")
        return
    await callback.message.answer(f"📦 Найдено {len(products)} товаров в категории:")
    await callback.message.answer(text="Выберете товар:", reply_markup=get_products_kb(products))
    await callback.message.delete()


@router.callback_query(F.data.startswith("products_page_"))
async def handle_products_navigation(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[2])

    products = get_products_by_category(session, category_id)
    keyboard = get_products_kb(products, page=page)

    await callback.message.edit_text(
        f"📦 Выберите продукт (страница {page + 1}):",
        reply_markup=keyboard
    )
    await callback.answer()