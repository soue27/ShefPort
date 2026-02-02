# middlewares/db.py
from datetime import date, datetime

from aiogram import BaseMiddleware
from sqlalchemy.orm import Session
from database.db import engine
from database.models import CostumerActivity, DeliveryMode


class DBSessionMiddleware(BaseMiddleware):

    async def __call__(self, handler, event, data):
        session = Session(engine)
        try:
            data["session"] = session
            return await handler(event, data)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


