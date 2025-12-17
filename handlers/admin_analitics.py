import os
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from loguru import logger
from sqlalchemy.orm import Session

from database.db import get_all_tables_names, export_data_to_excel
from keyboards.admin_kb import get_upload_kb

router = Router(name='admin_analitics')

user_cart_messages = {}


@router.callback_query(F.data == "upload_xlsx")
async def show_tables(callback: CallbackQuery):
    """Show tables to export."""
    await callback.message.answer("Выберите таблицу", reply_markup=get_upload_kb())


@router.callback_query(F.data.startswith("export_"))
async def export_table(callback: CallbackQuery, session: Session):
    """Export table to excel and send to admin
    :param callback: CallbackQuery
    :param session: Session
    """
    table_name = callback.data.split("_")[1]
    if table_name == "back":
        await callback.message.delete()
        return
    try:
        file_path = f"data/{table_name} {datetime.now().strftime("%d-%m-%y")}.xlsx"
        export_data_to_excel(session, table_name, file_path)
        document = FSInputFile(file_path)
        logger.info(f"Выгрузка для {callback.from_user.id} данных из таблицы {table_name} успешно")
    except Exception as e:
        logger.exception(f"Ошибка при выгрузке данных из таблицы {table_name} для {callback.from_user.id}: {e}")
        return
    await callback.message.answer_document(document=document, caption=f"Выгрузка данных из таблицы {table_name}")
    os.remove(file_path)


@router.callback_query(F.data == "get_log")
async def get_log(callback: CallbackQuery):
    """Send log files to admin
    :param callback: CallbackQuery
    """
    path = 'logs/'

    # Только файлы (исключая папки)
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    for file in files:
        try:
            file_path = os.path.join(path, file)
            document = FSInputFile(file_path)
            await callback.message.answer_document(document=document, caption=file)
            logger.info(f"Отправка логa {file} для {callback.from_user.id} успешно")
        except Exception as e:
            logger.exception(f"Ошибка при отправке лога {file} для {callback.from_user.id}: {e}")
            return


