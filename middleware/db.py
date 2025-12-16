# middlewares/db.py
from aiogram import BaseMiddleware
from sqlalchemy.orm import Session
from database.db import engine

class DBSessionMiddleware(BaseMiddleware):

    async def __call__(self, handler, event, data):
        session = Session(engine)
        try:
            data["session"] = session
            return await handler(event, data)
        finally:
            session.close()
