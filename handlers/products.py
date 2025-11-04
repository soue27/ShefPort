"""Module handlers.products

This module contains handlers for product interactions.

"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from datadase.db import get_product_description, session
from services.search import clean_description

router = Router(name='products_router')


# Обработчики действий с товарами
@router.callback_query(F.data.startswith("add_to_cart_"))
async def handle_add_to_cart(callback: CallbackQuery):
    """Обработчик добавления товара в корзину"""
    product_id = int(callback.data.split("_")[3])


    # cart_item = CartItem(user_id=callback.from_user.id, product_id=product_id)
    # session.add(cart_item)
    # await session.commit()

    await callback.answer("✅ Товар добавлен в корзину!")


@router.callback_query(F.data.startswith("description_"))
async def handle_add_favorite(callback: CallbackQuery):
    """Обработчик вывода на экран описания товара"""
    product_id = int(callback.data.split("_")[1])
    product = get_product_description(session, product_id)
    description = clean_description(product.description)
    await callback.message.answer_photo(photo=product.image, caption=product.name)
    await callback.message.answer(text= description, parse_mode="HTML")


@router.callback_query(F.data.startswith("quick_order_"))
async def handle_quick_order(callback: CallbackQuery):
    """Обработчик быстрого заказа"""
    product_id = int(callback.data.split("_")[2])
    await callback.answer("⚡ Запрос на быстрый заказ отправлен!")