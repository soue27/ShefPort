"""
Module handlers.search_helpers

This module contains helper functions for handling search functionality.
"""
import asyncio
from typing import List

from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import session, search_products
from handlers.product_helpers import send_product_card


async def send_search_results_batch(message: Message, products: List, offset: int = 0, batch_size: int = 5):
    """Отправляет порцию результатов поиска"""
    current_batch = products[offset:offset + batch_size]
    total_products = len(products)
    
    # Отправляем товары текущей порции
    for i, product in enumerate(current_batch, 1):
        current_index = offset + i
        await send_product_card(message, product, current_index, total_products)
        
        # Небольшая пауза между карточками для лучшего UX
        if i < len(current_batch):
            await asyncio.sleep(0.3)
    
    # Отправляем контроллер навигации, если есть что листать
    if len(products) > batch_size:
        keyboard = create_search_navigation_keyboard(offset, len(products), batch_size)
        await message.answer(
            f"Страница {offset // batch_size + 1} из {(len(products) - 1) // batch_size + 1}",
            reply_markup=keyboard.as_markup()
        )


def create_search_navigation_keyboard(current_offset: int, total_products: int, batch_size: int = 5):
    """Создает клавиатуру для навигации по результатам поиска"""
    keyboard = InlineKeyboardBuilder()
    
    # Кнопки навигации
    if current_offset > 0:
        keyboard.button(
            text="⬅️ Назад",
            callback_data=f"search_prev_{current_offset - batch_size}"
        )
    
    if current_offset + batch_size < total_products:
        keyboard.button(
            text="Вперед ➡️",
            callback_data=f"search_next_{current_offset + batch_size}"
        )
    
    return keyboard


class SearchState:
    """Класс для хранения состояния поиска"""
    def __init__(self, query: str, products: list):
        self.query = query
        self.products = products
        self.offset = 0


# Глобальный словарь для хранения состояния поиска (временное решение)
search_states = {}


def register_search_handlers(router):
    """Регистрирует обработчики поиска"""
    @router.callback_query(F.data.startswith('search_'))
    async def handle_search_navigation(callback: CallbackQuery):
        """Обработка навигации по результатам поиска"""
        user_id = callback.from_user.id
        if user_id not in search_states:
            await callback.answer("Сессия поиска истекла. Пожалуйста, выполните поиск снова.")
            return

        search_state = search_states[user_id]
        # Разбираем callback_data в формате 'search_prev_10' или 'search_next_10'
        parts = callback.data.split('_')
        if len(parts) >= 3:  # Если формат правильный: ['search', 'prev', '10']
            offset = int(parts[-1])  # Берем последнюю часть как offset
        else:
            offset = 0  # Значение по умолчанию, если что-то пошло не так

        # Удаляем предыдущее сообщение с пагинацией
        try:
            await callback.message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

        # Отправляем новую порцию товаров
        await send_search_results_batch(
            callback.message,
            search_state.products,
            offset=offset
        )
        await callback.answer()
