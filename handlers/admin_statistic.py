import os
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger
from sqlalchemy.orm import Session

from database.db import export_data_to_excel, count_model_records
from database.models import (Costumer, Cart, CartItems, Order, OrderItems,
                             CostumerActivity, News, Question)
from handlers.admin import send_file_to_admin
from keyboards.admin_kb import get_upload_kb, get_statistic_kb
from services.statistic import get_statistic_for_past_period, get_statistic_for_week, get_statistic_for_month
from services.updater_db import load_report, update_products_from_df


router = Router(name='admin_statistic')

#count_model_records

models_stat = [Costumer, Cart, CartItems, Order, OrderItems, CostumerActivity, News, Question]

MODEL_TITLES = {
    Costumer: "👤 Новых пользователей",
    Cart: "🛒 Новых корзин",
    CartItems: "📦 Товаров в корзинах",
    Order: "📑 Новых заказов",
    OrderItems: "📦 Позиции в заказах",
    CostumerActivity: "📊 Активность пользователей",
    News: "📰 Разослано новостей",
    Question: "❓ Поступило вопросов",
}


stat_days = ["За день", "За неделю", "За месяц", "За год"]


def build_stat_message(stats: dict, stat_days: list[str], session: Session) -> str:
    model_by_title = {title: model for model, title in MODEL_TITLES.items()}

    lines = ["📈 *Статистика за предыдущий:*\n"]

    for model, values in stats.items():
        model_name = model_by_title[model]
        count_all = count_model_records(session, model_name)
        lines.append(f"*{model}, всего: {count_all}*")
        for day, value in zip(stat_days, values):
            lines.append(f"  • {day} — {value}")
        lines.append("")

    return "\n".join(lines)


@router.callback_query(F.data == "statistic")
async def get_statistic(callback: CallbackQuery, session: Session):
    stats: dict [str, list[int]] = {}
    for model in models_stat:
        stats[model.__name__] = get_statistic_for_past_period(session, model)

    stats_prepared = {
        MODEL_TITLES[model]: get_statistic_for_past_period(session, model)
        for model in models_stat
    }
    message = build_stat_message(stats_prepared, stat_days, session)
    await callback.message.answer(message, parse_mode="Markdown")
    await callback.message.answer("Для вывода статистики за \nп"
                                  "рошедший период нажмите ↓", reply_markup=get_statistic_kb()
    )


@router.callback_query(F.data == "prev_weekly_stat")
async def get_statistic(callback: CallbackQuery, session: Session, bot: Bot):
    await get_statistic_for_week(session, bot)


@router.callback_query(F.data == "prev_monthly_stat")
async def get_statistic(callback: CallbackQuery, session: Session, bot: Bot):
    await get_statistic_for_month(session, bot)


@router.callback_query(F.data == "weekly_stat")
async def get_statistic(callback: CallbackQuery, session: Session, bot: Bot):
    await get_statistic_for_week(session, bot, current=True)


@router.callback_query(F.data == "prev_monthly_stat")
async def get_statistic(callback: CallbackQuery, session: Session, bot: Bot):
    await get_statistic_for_month(session, bot)


@router.callback_query(F.data == "monthly_stat")
async def get_statistic(callback: CallbackQuery, session: Session, bot: Bot):
    await get_statistic_for_month(session, bot, current=True)



