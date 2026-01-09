"""Module handlers.products

This module contains handlers for product interactions.

"""
import json

from aiogram import Router, F, types
from aiogram.types import CallbackQuery
from sqlalchemy.exc import SQLAlchemyError

from database.db import get_product_description, session
from keyboards.describe_kb import create_describe_keyboard
from services.search import clean_description
from loguru import logger

router = Router(name='products_router')

message_store = {}




# Обработчики действий с товарами

@router.callback_query(F.data.startswith("description_"))
async def show_description(callback: CallbackQuery):
    """Обработчик вывода на экран описания товара"""
    try:
        product_id = int(callback.data.split("_")[1])
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} преобразование номера товара {callback.data.split("_")[1]} в целое "
            f"  в 'show_description' выполнен неуспешно: {e}"
        )
        return
    if callback.data.split("_")[2] == "True":
        order = True
    else:
        order = False
    try:
        product = get_product_description(session, product_id)
        logger.info(
            f"'show_description':  {callback.from_user.id} получил данные 'get_product_description' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_product_description' "
            f"  в 'show_description' выполнен неуспешно: {e}"
        )
        return

    description = clean_description(product.description)
    if len(product.characteristics) > 2:
        description += "\nХарактеристики:"
        opisan = json.loads(product.characteristics)
        for k, v in opisan.items():
            description += f"\n {k} - {v}"
    photo_msg = await callback.message.answer_photo(photo=product.image, caption=f"{product.name},\n<b>💰цена: {product.price} руб.</b>")
    desc_msg = await callback.message.answer(text= description, parse_mode="HTML", reply_markup=create_describe_keyboard(product_id, order).as_markup())
    message_store["msg_id"] = [photo_msg.message_id, desc_msg.message_id]
    await callback.answer("Важное сообщение!", show_alert=False)


@router.callback_query(F.data.startswith('close_describe'))
async def close_describe(callback: types.CallbackQuery):
    """Callback handler to close the description of a product.
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