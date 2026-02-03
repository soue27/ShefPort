from datetime import datetime, date, timezone

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from sqlalchemy.orm import Session

from database.db import count_model_records, session
from database.models import (Costumer, Cart, CartItems, Order, OrderItems,
                             CostumerActivity, News, Question, DeliveryMode)
from keyboards.admin_kb import get_statistic_kb
from services.statistic import get_statistic_for_past_period, get_statistic_for_week, get_statistic_for_month


router = Router(name='admin_delivery')


class DeliveryTime(StatesGroup): #Стейт для ввода артикля товара
    delivery_time = State()


@router.callback_query(F.data == "delivery_on")
async def get_statistic_prev_monthly(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите время работы доставки в формате 10.00-20.00")
    await state.set_state(DeliveryTime.delivery_time)


@router.message(DeliveryTime.delivery_time)
async def get_delivery_time(message: Message, state: FSMContext):
    try:
        start, end = message.text.split("-")
    except Exception as e:
        print(f"error {e}")
        await message.answer("Введите время в верном формате 10.00-20.00")
        await state.set_state(DeliveryTime.delivery_time)
        return
    start = datetime.strptime(
        f"{date.today()} {start.replace('.', ':')}",
        "%Y-%m-%d %H:%M"
    ).replace(tzinfo=timezone.utc)
    end = datetime.strptime(
        f"{date.today()} {end.replace('.', ':')}",
        "%Y-%m-%d %H:%M"
    ).replace(tzinfo=timezone.utc)
    mode = session.get(DeliveryMode, 1)
    if not mode:
        mode = DeliveryMode(id=1, is_enabled=True)
        session.add(mode)
    mode.start_at = start  # или строка: f"{start_time:%H:%M}"
    mode.end_at = end # или строка: f"{end_time:%H:%M}"
    mode.is_enabled = True
    session.commit()
    await message.answer(f"Доставка включена в период c {start} до {end} часов")
    await state.clear()


@router.callback_query(F.data == "delivery_off")
async def get_statistic_prev_monthly(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Доставка отключена")
    mode = session.get(DeliveryMode, 1)
    if not mode:
        mode = DeliveryMode(id=1, is_enabled=False)
        session.add(mode)
    mode.is_enabled = False
    session.commit()


