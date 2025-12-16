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
    await callback.message.answer("Выберите таблицу", reply_markup=get_upload_kb())


@router.callback_query(F.data.startswith("export_"))
async def export_table(callback: CallbackQuery, session: Session, bot: Bot):
    table_name = callback.data.split("_")[1]
    if table_name == "back":
        await callback.message.delete()
        return
    file_path = f"data/{table_name} {datetime.now().strftime("%d-%m-%y")}.xlsx"
    export_data_to_excel(session, table_name, file_path)
    document = FSInputFile(file_path)
    await callback.message.answer_document(document=document, caption=f"Выгрузка данных из таблицы {table_name}")
    # with open(file_path, 'rb') as f:
    #     await callback.message.answer_document(document=f)
    os.remove(file_path)


