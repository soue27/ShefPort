from datetime import datetime, date, timezone, timedelta
from zoneinfo import ZoneInfo

from aiogram import BaseMiddleware
from aiogram.client import bot
from aiogram.types import TelegramObject, CallbackQuery
from sqlalchemy.orm import Session
from database.models import CostumerActivity, DeliveryMode
from database.db import engine
from database.db import is_delivery_available, is_first_user_action_today
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton


class DeliveryNotificationMiddleware(BaseMiddleware):
    """Middleware, который уведомляет пользователя о доступной доставке один раз в день"""

    def __init__(self):
        session = Session(engine)

    async def __call__(self, handler, event: TelegramObject, data: dict):
        session = Session(engine)
        try:
            # ekb_tz = ZoneInfo("Asia/Yekaterinburg")
            user = getattr(event, "from_user", None)
            if not user:
                return await handler(event, data)

            chat_id = user.id
            today = date.today()
            # now = datetime.now(tz=ekb_tz)
            now = datetime.now()
            # Получаем текущий режим доставки
            mode = session.get(DeliveryMode, 1)
            if not mode or not mode.is_enabled:
                return await handler(event, data)

            # Проверяем доступность доставки
            delivery_available = is_delivery_available(mode, now)
            data["delivery_available"] = delivery_available
            data["delivery_mode"] = mode
            # mode.start_at = mode.start_at + timedelta(hours=5)
            # mode.end_at = mode.end_at + timedelta(hours=5)
            # Если доставка доступна и это первое действие пользователя
            if delivery_available and is_first_user_action_today(session, chat_id, today):
                # Показываем всплывающее сообщение с кнопкой
                if isinstance(event, CallbackQuery):
                    # Для колбэка — настоящий алерт в центре
                    await event.answer(
                        f"🚚 Доставка сегодня доступна с "
                        f"{mode.start_at:%H:%M} до {mode.end_at:%H:%M}!",
                        show_alert=True
                    )
                    # В aiogram 3 один вызов answer() достаточно — "часики" автоматически снимаются

                elif isinstance(event, Message):
                    # Для сообщения — отправляем сообщение с кнопкой-триггером
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="ℹ️ Подробнее о доставке",
                                callback_data="delivery_alert_info"
                            )
                        ]
                    ])
                    await event.answer(
                        f"🚚 Доставка сегодня доступна с {mode.start_at:%H:%M} до {mode.end_at:%H:%M}!",
                        reply_markup=kb
                    )
            return await handler(event, data)

        finally:
            pass
            #session.close()
