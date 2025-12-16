from loguru import logger
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from aiogram import BaseMiddleware
from sqlalchemy.orm import Session

# from models import User, UserActivity
from datetime import datetime

from database.db import get_costumer_id
from database.models import CostumerActivity


class UserActivityMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        session: Session = data.get("session")
        if not session:
            return await handler(event, data)

        # Сообщения
        if isinstance(event, Message):
            payload = event.text
            event_type = "message"
            user_id = event.from_user.id
            chat_id = event.chat.id

        # Нажатия кнопок
        elif isinstance(event, CallbackQuery):
            payload = event.data
            event_type = "callback_query"
            user_id = event.from_user.id
            chat_id = event.message.chat.id if event.message else event.from_user.id

        else:
            return await handler(event, data)

        # # DEBUG
        # print("==== USER ACTIVITY RAW ====")
        # print("USER:", user_id)
        # print("CHAT:", chat_id)
        # print("EVENT TYPE:", event_type)
        # print("PAYLOAD:", payload)
        # print("===========================")

        user_id = get_costumer_id(session, user_id)
        print(user_id)

        # Запись как есть
        activity = CostumerActivity(
            user_id=user_id,
            chat_id=chat_id,
            event_type=event_type,
            action=payload,
            payload=payload,
            created_at=datetime.now(timezone.utc),  # <- timezone-aware UTC
            activity_date=datetime.now(timezone.utc).date(),
            week=datetime.now(timezone.utc).isocalendar().week,
            month=datetime.now(timezone.utc).month,
            year=datetime.now(timezone.utc).year
        )
        session.add(activity)
        session.commit()

        return await handler(event, data)

