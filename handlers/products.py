"""Module handlers.products

This module contains handlers for product interactions.

"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

router = Router(name='products_router')


# Обработчики действий с товарами
@router.callback_query(F.data.startswith("add_to_cart_"))
async def handle_add_to_cart(callback: CallbackQuery, session: AsyncSession):
    """Обработчик добавления товара в корзину"""
    product_id = int(callback.data.split("_")[3])


    # cart_item = CartItem(user_id=callback.from_user.id, product_id=product_id)
    # session.add(cart_item)
    # await session.commit()

    await callback.answer("✅ Товар добавлен в корзину!")


@router.callback_query(F.data.startswith("add_favorite_"))
async def handle_add_favorite(callback: CallbackQuery):
    """Обработчик добавления в избранное"""
    product_id = int(callback.data.split("_")[2])
    await callback.answer("💖 Товар добавлен в избранное!")


@router.callback_query(F.data.startswith("quick_order_"))
async def handle_quick_order(callback: CallbackQuery):
    """Обработчик быстрого заказа"""
    product_id = int(callback.data.split("_")[2])
    await callback.answer("⚡ Запрос на быстрый заказ отправлен!")