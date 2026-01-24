import os
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger
from sqlalchemy.orm import Session

from database.db import export_data_to_excel
from handlers.admin import send_file_to_admin
from keyboards.admin_kb import get_upload_kb
from services.updater_db import load_report, update_products_from_df

router = Router(name='admin_analitics')

user_cart_messages = {}


class LoadOstatki(StatesGroup):
    """
    Состояния для обработки ответов на вопросы пользователей.
    """
    getfile = State()


from sqlalchemy.exc import SQLAlchemyError

def commit_session(session):
    """Коммитим изменения с обработкой ошибок и откатом при исключении."""
    try:
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(f"Ошибка при коммите сессии: {e}")
        raise


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


@router.callback_query(F.data == "load_ostatki")
async def load_ostatki(callback: CallbackQuery, state: FSMContext):
    """Функция обработки нажатия меню для загрузки остатоков по складам"""
    await callback.message.answer("Загрузите файл .xlsx с остатками товара в бот")
    await state.set_state(LoadOstatki.getfile)


@router.message(LoadOstatki.getfile, F.document.file_name.endswith(".xlsx"))
async def load_ostatki_file(message: Message, state: FSMContext, bot: Bot, session: Session):
    """Функция загрузки документа с остатками"""
    document = message.document
    file = await message.bot.get_file(document.file_id)
    file_path = "data/report.xls"
    await message.bot.download_file(file.file_path, destination=file_path)
    df = load_report()
    count = update_products_from_df(df=df, session=session)
    try:
        if bot and count > 0:  # Only try to send file if bot instance is provided
            await send_file_to_admin("data/output.xlsx", bot)
            logger.info("Файл отправлен админу")
    except Exception as e:
        logger.exception(f"Ошибка при отправке файла админу: {e}")
    await state.clear()


@router.message(LoadOstatki.getfile, F.document)
async def load_ostatki_error(message: Message, state: FSMContext):
    await message.answer("Файл должен быть разрешением .xlsx")

