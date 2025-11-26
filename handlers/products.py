"""Module handlers.products

This module contains handlers for product interactions.

"""
import json

from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_product_description, session
from keyboards.describe_kb import create_describe_keyboard
from services.search import clean_description

router = Router(name='products_router')

message_store = {}

# Обработчики действий с товарами

@router.callback_query(F.data.startswith("description_"))
async def show_description(callback: CallbackQuery):
    """Обработчик вывода на экран описания товара"""
    product_id = int(callback.data.split("_")[1])
    if callback.data.split("_")[2] == "True":
        order = True
    else:
        order = False
    print(order)
    product = get_product_description(session, product_id)
    description = clean_description(product.description)
    print(len(product.characteristics), product.characteristics)
    if len(product.characteristics) > 2:
        description += "\nХарактеристики:"
        opisan = json.loads(product.characteristics)
        for k, v in opisan.items():
            description += f"\n {k} - {v}"
    photo_msg = await callback.message.answer_photo(photo=product.image, caption=f"{product.name},\n<b>💰цена: {product.price} руб.</b>")
    desc_msg = await callback.message.answer(text= description, parse_mode="HTML", reply_markup=create_describe_keyboard(product_id, order).as_markup())
    message_store["msg_id"] = [photo_msg.message_id, desc_msg.message_id]
    await callback.answer("Важное сообщение!", show_alert=False)
    print(message_store)



@router.callback_query(F.data.startswith('close_describe'))
async def close_describe(callback: types.CallbackQuery):
    """
    Callback handler to close the description of a product.

    Deletes the photo and description messages associated with the product.
    """
    msg_ids = message_store["msg_id"]
    if msg_ids:
        photo_id, desc_id = msg_ids
    try:
        await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=photo_id)
        await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=desc_id)
    except Exception as e:
        print(e, "message not deleted")
    del message_store["msg_id"]


@router.callback_query(F.data.startswith("quick_order_"))
async def handle_quick_order(callback: CallbackQuery):
    """Обработчик быстрого заказа"""
    product_id = int(callback.data.split("_")[2])
    await callback.answer("⚡ Запрос на быстрый заказ отправлен!")