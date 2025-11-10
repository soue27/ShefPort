from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from services.filters import IsAdmin


router = Router(name='admin')


@router.message(Command("admin"), IsAdmin())
async def admin_start(message: Message):
    await message.answer(f"Привет! Добро пожаловать Админ {message.from_user.full_name}")