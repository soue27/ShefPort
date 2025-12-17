import os
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from loguru import logger
from mypy.server.objgraph import method_wrapper_type
from sqlalchemy.orm import Session

from database.db import get_all_tables_names, export_data_to_excel, session, get_product_by_article, entity_to_excel
from keyboards.admin_kb import get_upload_kb, get_product_change_kb

router = Router(name='admin_product')

class ViewProduct(StatesGroup):
    article = State()


@router.callback_query(F.data == "view_product")
async def get_product_article(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажати кнопки 'просмотр товара
    :param
        callback
        state
    """
    await callback.message.answer("Введите артикул товара:")
    await state.set_state(ViewProduct.article)


@router.message(ViewProduct.article)
async def view_product(message: Message, state: FSMContext):
    """Обработчик ввода артикула товара, поиск товара в БД и отправка юзеру"""
    data = await state.get_data()
    article = message.text
    print(article)
    try:
        tovar = get_product_by_article(session, article)
        logger.info(f"'view_product' Товар {article} загружен для {message.from_user.id}")
    except Exception as e:
        logger.error(f"'view_product'  Ошибка при загрузке товара {article} для {message.from_user.id}: {e}")
        await message.answer("Ошибка при поиске товара")
        return
    if not tovar:
        await message.answer(f"Товар с артикулом {article} не найден\n"
                             f"Введите правильный артикул")
        await state.set_state(ViewProduct.article)
        logger.info(f"Товар {article} не найден для {message.from_user.id}")
        return
    try:
        file_name = entity_to_excel(tovar)
        await message.answer_document(FSInputFile(file_name))
        text = (f"Артикль: <b>{tovar.article}</b>\n"
                             f"Название: <b>{tovar.name}</b>\n"
                             f"Цена: <b>{tovar.price}</b>\n"
                             f"Единицы: <b>{tovar.unit}</b>\n"
                             f"Остаток: <b>{tovar.ostatok}</b>\n"
                             f"Описание: <b>{tovar.description}</b>\n"
                             f"Фото: <b>{tovar.main_image}</b>\n")
        await message.answer(text=text, reply_markup=get_product_change_kb(tovar.id, tovar.article))
        print(tovar.id)
        logger.info(f"Товар {article} загружен в файл для {message.from_user.id}")
        os.remove(file_name)
    except Exception as e:
        logger.error(f"Ошибка при загрузке товара {article} для {message.from_user.id}: {e}")
    finally:
        await state.clear()

