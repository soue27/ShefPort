"""Module handlers.carts

This module contains handlers for cart interactions.
"""
from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from data.config import SUPERADMIN_ID
from database.db import get_new_questions, session, get_question_by_id, save_answer, get_all_costumer_for_mailing, \
    save_news, get_active_cart, set_active_cart
from keyboards.admin_kb import main_kb, check_questions, get_questions, mailing_kb, confirm_kb
from services.filters import IsAdmin


router = Router(name='carts')


@router.message(F.text == '🛒 Моя корзина')
async def show_carts(message: Message):
    """Обработчик нажатия кнопки Моя корзина"""
    nomer = get_active_cart(session, message.from_user.id)
    if not nomer:
        await message.answer(text="Ваша корзина пуста, выберите товары", show_alert=True)
    else:
        await message.answer(text=f"В вашей корзине есть товары, в путь Корзина №{nomer}", show_alert=True)


@router.callback_query(F.data.startswith('add_to_cart_'))
async def show_product_bycategory(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[3])
    print(product_id)
    if not get_active_cart(session, callback.from_user.id):
         cart_id = set_active_cart(session, callback.from_user.id)
         await callback.answer(text=f"Товар добавлен в корзину {cart_id}", show_alert=True)



