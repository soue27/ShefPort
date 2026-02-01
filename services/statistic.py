"""
Module services.stat

This module contains analytics functions for counting various entities over different time periods.
"""
import os
from datetime import datetime, timedelta, time
from typing import Type

import calendar

import pandas as pd
from aiogram import Bot
from sqlalchemy.orm import  Session

from database.models import (Costumer, Cart, Order, CartItems, OrderItems,
                             CostumerActivity, AbstractBase, News, Question)
from database.db import count_model_records

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


def save_stat_to_excel(days: list, stats: dict, week: bool) -> str:
    """Функция сохранения статистики в файл ексель
    :param days: список с днями статистики для формирования столбца
    :param stats: словарь с реузльтатами статистики
    :param week: True если отчет за неделю, False - если за месяц
    """
    df = pd.DataFrame(index=days)

    # Заполняем DataFrame по моделям
    for model_name, entries in stats.items():
        df[model_name] = [entry["count"] for entry in entries]
    df["Всего"] = df.sum(axis=1)
    total_row = df.sum(axis=0)
    total_row.name = "Всего"

    # Добавляем строку с итогом
    df = pd.concat([df, total_row.to_frame().T])
    if week:
        data = days[0].strftime("%d.%m.%Y")
        file_path = f"data/statistics_week_{data}.xlsx"
    else:
        file_path = f"data/statistics_month_{days[0].month}_{days[0].year}.xlsx"
    # Сохраняем в Excel
    df.to_excel(file_path)
    return file_path


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


def get_statistic_for_past_period(
        session: Session,
        model: Type[AbstractBase],
        delta: timedelta = timedelta(days=0)
) -> list[int]:
    """Формирование статистики за предыдущий период от текущего дня
    периоды в днях берутся из stat_days"""
    count = []
    now = datetime.now()
    for day in stat_days:
        past_time = now.date() - timedelta(days=day)
        past_time = datetime.combine(past_time, datetime.min.time())
        now = past_time + timedelta(days=day)
        count.append(count_model_records(
            session,
            model,
            filters=[model.created_at >= past_time, model.created_at <= now])
        )
    return count


async def get_statistic_for_week(session: Session, bot: Bot, current: bool = False, tg_id: int = None):
    """
    Функция для сбора еженедельной статистики.
    :param session: Сессия для работы с базой данных
    :type session: sqlalchemy orm Session
    :param bot: экземпляр бота для отправки файла с результатами статистики
    :type bot: aiogram Bot
    :param current: Если False, то статистика собирается за предыдущую неделю от текущей даты
    :type current: bool
    :param tg_id: Если имеется значение, то файл отправляется по тг ай ди, статистика была запрошена по кнопке
    :type tg_id: int
    """
    count: list[dict] = []
    stats: dict[str, list[int]] = {}
    #Вычисление даты первого дня предыдущей недели
    today = datetime.now().date()
    if not current:
        #Определение дат для предыдущей недели
        start_week = datetime.now().date() - timedelta(days=today.isoweekday() -1)
        start_prev_week = start_week - timedelta(days=7)
        # Вычисление даты и времени первого дня предыдущей недели
        start = datetime.combine(start_prev_week, datetime.min.time())
        end = datetime.combine(start_prev_week + timedelta(days=7), datetime.min.time())
    else:
        # Определение дат для текущей недели
        start_week = datetime.now().date() - timedelta(days=today.isoweekday() - 1)
        start_prev_week = start_week
        # Вычисление даты и времени первого дня предыдущей недели
        start = datetime.combine(start_prev_week, datetime.min.time())
        end = datetime.combine(start_prev_week + timedelta(days=7), datetime.min.time())
    # Формирование словаря с результатами запроса
    for model in models_stat:
        for day_start, day_end in iterate_days(start, end):
            c = count_model_records(session, model, filters=[model.created_at >= day_start, model.created_at <= day_end])
            count.append({"date": day_start, "count": c})
        stats[MODEL_TITLES[model]] = count
        count: list[dict] = []
    dates = [entry["date"].date() for entry in next(iter(stats.values()))]
    file_path_activity = await get_statistic_for_activity(session, bot, start_day=start, end_day=end)
    # Формирование фапйла с результатами статистики.
    # Создаём пустой DataFrame с индексом = даты
    week = True
    file_path = save_stat_to_excel(dates, stats, week)
    if tg_id:
        await send_file_to_admin(file_path, bot, tg_id)
        await send_file_to_admin(file_path_activity, bot, tg_id)
    else:
        await send_file_to_admin(file_path, bot)
        await send_file_to_admin(file_path_activity, bot)
    os.remove(file_path)
    os.remove(file_path_activity)


async def get_statistic_for_month(session: Session, bot: Bot, current: bool = False, tg_id: int = None):
    count: list[dict] = []
    stats: dict[str, list[int]] = {}
    month = datetime.now().month
    if not current:
        #Определение месяца для предыдущего периода
        prev_month = 12 if month == 1 else month - 1
    else:
        # Определение месяца для текущего периода
        prev_month = month
    if prev_month == 12:
        year = datetime.now().year - 1
    else:
        year = datetime.now().year
    days_in_month = calendar.monthrange(year, prev_month)[1]
    days_list = [
        datetime(year, prev_month, day, 0, 0, 0)
        for day in range(1, days_in_month + 1)
    ]
    for model in models_stat:
        for day in days_list:
            c = count_model_records(session, model, filters=[model.created_at >= day, model.created_at <= day + timedelta(days=1)])
            count.append({"date": day, "count": c})
        stats[MODEL_TITLES[model]] = count
        count: list[dict] = []
    # Формирование фапйла с результатами статистики.
    # Создаём пустой DataFrame с индексом = даты
    file_path_activity = await get_statistic_for_activity(session, bot, start_day=days_list[0], end_day=days_list[-1])
    week = False
    file_path = save_stat_to_excel(days_list, stats, week)
    if tg_id:
        await send_file_to_admin(file_path, bot, tg_id)
        await send_file_to_admin(file_path_activity, bot, tg_id)
    else:
        await send_file_to_admin(file_path, bot)
        await send_file_to_admin(file_path_activity, bot)
    os.remove(file_path)
    os.remove(file_path_activity)


async def get_statistic_for_activity(session: Session, bot: Bot, start_day: datetime, end_day: datetime):
    key_words: dict = {
        "🐠 Категории товаров": "Открытий каталога",
        "📝 Написать сообщение": "Направлено сообщений в магазин",
        "🔎 Поиск товара": "Количество поиска товаров",
        "🛍  Мои заказы": "Нажатия меню Мои заказы",
        "🛒 Моя корзина": "Нажатия меню Моя корзина",
        "cart": "Действий внутри корзины",
        "cartitem": "Действия с товарами в корзины",
        "order": "Действий внутри заказа",
        "orderitem": "Действия с товарами в заказа",
        "catalog": "Действий в каталоге",
        "category": "Выбрано категорий в каталоге",
        "in_stock": "Выбрано показов товара в Наличии",
        "show_all": "Выбрано показов всех товаров"
    }

    results = []

    for keyword, description in key_words.items():
        filters = [CostumerActivity.created_at >= start_day,
                  CostumerActivity.created_at <= end_day,
                   CostumerActivity.payload.like(f"%{keyword}%")
        ]

        count = count_model_records(session=session, model=CostumerActivity, filters=filters)

        results.append({
            "Ключевое слово": keyword,
            "Описание": description,
            "Количество": count
        })

    df = pd.DataFrame(results)

    file_path = (
        f"data/activity_statistic_"
        f"{start_day:%Y-%m-%d}_{end_day:%Y-%m-%d}.xlsx"
    )

    df.to_excel(file_path, index=False)

    return file_path