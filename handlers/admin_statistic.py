"""
Модуль для обработки административных функций статистики в Telegram боте.

Этот модуль содержит обработчики для просмотра и экспорта статистики по различным моделям данных:
- пользователи, корзины, заказы, товары, активность пользователей, новости и вопросы

Основные функции:
- Формирование и отображение статистики за различные периоды (день, неделя, месяц, год)
- Экспорт статистических данных в Excel файлы
- Обработка callback-запросов для получения детальной статистики

Используемые модели:
- Costumer, Cart, CartItems, Order, OrderItems, CostumerActivity, News, Question

Зависимости:
- aiogram для работы с Telegram Bot API
- SQLAlchemy для работы с базой данных
- loguru для логирования
- Сервисы statistic и updater_db для бизнес-логики
"""



from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.orm import Session

from database.db import count_model_records
from database.models import (Costumer, Cart, CartItems, Order, OrderItems,
                             CostumerActivity, News, Question)
from keyboards.admin_kb import get_statistic_kb
from services.statistic import get_statistic_for_past_period, get_statistic_for_week, get_statistic_for_month


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


def build_stat_message(stats: dict, list_days: list[str], session: Session) -> str:
    """
    Формирует отформатированное сообщение со статистикой для отправки в Telegram.

    Args:
        stats (dict): Словарь со статистическими данными, где ключ - название модели,
                     а значение - список значений за разные периоды
        list_days (list[str]): Список периодов для отображения статистики
                              (например, ["За день", "За неделю", "За месяц", "За год"])
        session (Session): Сессия SQLAlchemy для работы с базой данных

    Returns:
        str: Отформатированное сообщение со статистикой в Markdown формате,
             готовое для отправки в Telegram
    """
    model_by_title = {title: model for model, title in MODEL_TITLES.items()}

    lines = ["📈 *Статистика за предыдущий:*\n"]

    for model, values in stats.items():
        model_name = model_by_title[model]
        count_all = count_model_records(session, model_name)
        lines.append(f"*{model}, всего: {count_all}*")
        for day, value in zip(list_days, values):
            lines.append(f"  • {day} — {value}")
        lines.append("")

    return "\n".join(lines)


@router.callback_query(F.data == "statistic")
async def get_statistic(callback: CallbackQuery, session: Session):
    """
    Обработчик callback-запроса для получения общей статистики по всем моделям.

    Функция собирает статистические данные за предыдущие периоды (день, неделя, месяц, год)
    по всем зарегистрированным моделям, формирует отформатированное сообщение и отправляет
    его пользователю в Telegram. Также предоставляет клавиатуру для получения детальной
    статистики за конкретные периоды.

    Args:
        callback (CallbackQuery): Callback-запрос от Telegram с данными "statistic"
        session (Session): Сессия SQLAlchemy для работы с базой данных

    Returns:
        None

    Side effects:
        - Отправляет сообщение со статистикой в чат Telegram
        - Отправляет дополнительное сообщение с клавиатурой для детальной статистики
        - Выполняет запросы к базе данных для получения статистических данных
    """
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
async def get_statistic_prev_weekly(callback: CallbackQuery, session: Session, bot: Bot):
    tg_id = callback.from_user.id
    await get_statistic_for_week(session, bot, tg_id=tg_id)


@router.callback_query(F.data == "prev_monthly_stat")
async def get_statistic_prev_monthly(callback: CallbackQuery, session: Session, bot: Bot):
    tg_id = callback.from_user.id
    await get_statistic_for_month(session, bot, tg_id=tg_id)
    print(callback.from_user.id)


@router.callback_query(F.data == "weekly_stat")
async def get_statistic_weekly(callback: CallbackQuery, session: Session, bot: Bot):
    tg_id = callback.from_user.id
    await get_statistic_for_week(session, bot, current=True, tg_id=tg_id)


@router.callback_query(F.data == "monthly_stat")
async def get_statistic(callback: CallbackQuery, session: Session, bot: Bot):
    tg_id = callback.from_user.id
    await get_statistic_for_month(session, bot, current=True, tg_id=tg_id)



