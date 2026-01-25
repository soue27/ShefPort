"""
Module services.stat

This module contains analytics functions for counting various entities over different time periods.
"""
import os
from datetime import datetime, timedelta, date, time
from typing import Union, Type

import pandas as pd
from aiogram import Bot
from sqlalchemy import func, and_, extract
from sqlalchemy.orm import DeclarativeBase, Session

from database.models import (Costumer, Cart, Order, CartItems, OrderItems,
                             CostumerActivity, AbstractBase, News, Question)
from database.db import session, count_model_records, Base
import zoneinfo

from handlers.admin import send_file_to_admin

stat_days = [1, 7, 30, 365]
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

def iterate_days(start_date: datetime, end_date: datetime):
    """
    Генератор, который проходит по всем дням от start_date до end_date (включительно),
    возвращает кортеж (start_of_day, end_of_day) для каждого дня.
    """
    current_date = start_date
    while current_date < end_date:
        start_of_day = datetime.combine(current_date, time.min)  # 00:00:00
        end_of_day = datetime.combine(current_date, time.min) + timedelta(days=1)  # 00:00 следующего дня
        yield start_of_day, end_of_day
        current_date += timedelta(days=1)


def get_statistic_for_past_period(session: Session, model: Type[AbstractBase], delta: timedelta = timedelta(days=0)) -> list[int]:
    count = []
    now = datetime.now()
    for day in stat_days:
        past_time = now.date() - timedelta(days=day)
        past_time = datetime.combine(past_time, datetime.min.time())
        now = past_time + timedelta(days=day)
        count.append(count_model_records(session, model, filters=[model.created_at >= past_time, model.created_at <= now]))
    return count


async def get_statistic_for_week(session: Session, bot: Bot):
    count: list[dict] = []
    stats: dict[str, list[int]] = {}
    today = datetime.now().date()
    week = datetime.now().isocalendar()[1]
    start_week = datetime.now().date() - timedelta(days=today.isoweekday() -1)
    start_prev_week = start_week - timedelta(days=7)
    start = datetime.combine(start_prev_week, datetime.min.time())
    end = datetime.combine(start_prev_week + timedelta(days=7), datetime.min.time())
    days = iterate_days(start, end)
    for model in models_stat:
        for day_start, day_end in iterate_days(start, end):
            c = count_model_records(session, model, filters=[model.created_at >= day_start, model.created_at <= day_end])
            count.append({"date": day_start, "count": c})
        stats[MODEL_TITLES[model]] = count
        count: list[dict] = []
    dates = [entry["date"].date() for entry in next(iter(stats.values()))]

    # Создаём пустой DataFrame с индексом = даты
    df = pd.DataFrame(index=dates)

    # Заполняем DataFrame по моделям
    for model_name, entries in stats.items():
        df[model_name] = [entry["count"] for entry in entries]
    df["Всего"] = df.sum(axis=1)
    total_row = df.sum(axis=0)
    total_row.name = "Всего"

    # Добавляем строку с итогом
    df = pd.concat([df, total_row.to_frame().T])

    # Сохраняем в Excel
    file_path = f"data/statistics_week_{start.date()}.xlsx"
    df.to_excel(file_path)
    await send_file_to_admin(file_path, bot)
    os.remove(file_path)

