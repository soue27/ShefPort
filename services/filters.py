from aiogram.filters import BaseFilter
from aiogram.types import Message

from datadase.db import is_admin, session


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message):
        return is_admin(session, message.from_user.id)
