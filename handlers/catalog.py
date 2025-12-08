"""
Module handlers.catalog

This module contains handlers for catalog navigation.

"""
from aiogram import Router, F
from aiogram.types import  CallbackQuery
from sqlalchemy.orm import Session

from loguru import logger

from handlers.product_helpers import send_products_batch
from database.db import get_products_by_category, session
from keyboards.catalog_control import create_pause_keyboard

router = Router(name='catalog_router')


# Обработчики навигации по каталогу
@router.callback_query(F.data.startswith("catalog_continue_"))
async def handle_continue_catalog(callback: CallbackQuery):
    """Обработчик продолжения просмотра каталога"""
    _, _, category_id, offset = callback.data.split("_")
    try:
        category_id = int(category_id)
        offset = int(offset)
    except Exception as e:
        logger.exception(
            f" Ошибка преобразования ай ди категории в 'handle_continue_catalog': {e}"
        )
        return

    # Удаляем старое сообщение с контролем
    await callback.message.delete()

    # Получаем товары и показываем следующую порцию
    try:
        products = get_products_by_category(session, category_id)
        logger.info(
            f"'catalog.handle_continue_catalo: пользователь {callback.from_user.id} получил данные 'get_products_by_category' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_products_by_category'"
            f"  в 'catalog.handle_continue_catalog' выполнен неуспешно: {e}"
        )
        return
    await send_products_batch(callback.message, products, category_id, offset)

    await callback.answer()


@router.callback_query(F.data.startswith("catalog_pause_"))
async def handle_pause_catalog(callback: CallbackQuery):
    """Обработчик паузы в просмотре каталога"""
    _, _, category_id, offset = callback.data.split("_")

    pause_keyboard = create_pause_keyboard(int(category_id), int(offset))

    await callback.message.edit_text(
        "⏸️ <b>Просмотр приостановлен</b>\n\n"
        "Вы можете продолжить просмотр когда будете готовы",
        parse_mode="HTML",
        reply_markup=pause_keyboard.as_markup()
    )

    await callback.answer("Просмотр приостановлен")


@router.callback_query(F.data == "catalog_close")
async def handle_close_catalog(callback: CallbackQuery):
    """Обработчик закрытия каталога"""
    await callback.message.delete()
    await callback.message.answer(
        "👋 <b>Просмотр товаров завершен</b>\n"
        "Возвращайтесь в любое время!",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "catalog_change_category")
async def handle_change_category(callback: CallbackQuery):
    """Обработчик смены категории"""
    await callback.message.edit_text(
        "🔄 <b>Возврат к выбору категории</b>\n"
        "Используйте команду /categories для выбора новой категории",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("catalog_skip_"))
async def handle_skip_products(callback: CallbackQuery, session: Session):
    """Обработчик пропуска товаров"""
    _, _, category_id, offset = callback.data.split("_")
    try:
        category_id = int(category_id)
    except Exception as e:
        logger.exception(
            f" Ошибка преобразования ай ди категории в 'handle_skip_products': {e}"
        )
        return
    offset = int(offset)

    # Удаляем старое сообщение с контролем
    await callback.message.delete()

    # Получаем товары и показываем следующую порцию после пропуска
    try:
        products = get_products_by_category(session, category_id)
        logger.info(
        f"'catalog.handle_skip_products: пользователь {callback.from_user.id} получил данные 'get_products_by_category' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_products_by_category'"
            f"  в 'catalog.handle_skip_products' выполнен неуспешно: {e}"
        )
        return
    await send_products_batch(callback.message, products, category_id, offset)

    await callback.answer("🚀 Пропущено 20 товаров")


@router.callback_query(F.data == "catalog_complete")
async def handle_catalog_complete(callback: CallbackQuery):
    """Обработчик завершения просмотра всех товаров"""
    await callback.message.edit_text(
        "🎉 <b>Поздравляем! Вы просмотрели все товары в этой категории!</b>\n\n"
        "Можете выбрать другую категорию или вернуться позже.",
        parse_mode="HTML"
    )
    await callback.answer()