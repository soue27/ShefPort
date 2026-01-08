import os
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from loguru import logger

from database.db import session, get_all_admin, export_data_to_excel, set_admin
from keyboards.admin_kb import get_set_admins

router = Router(name='admin_setadmin')


class SetAdmin(StatesGroup):
    admin_id = State()


@router.callback_query(F.data == "view_admins")
async def get_product_article(callback: CallbackQuery, state: FSMContext):
    admins = get_all_admin(session)
    print(admins)
    await callback.message.answer("Текущие админы:")
    for admin in admins:
        await callback.message.answer(f"<b>ID: {admin}</b>", parse_mode="HTML")
    await callback.message.answer("Выберите действие:", reply_markup=get_set_admins())


@router.callback_query(F.data == "deleteadmin")
async def delete_admin(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ID админа:")
    await state.update_data(action='delete')
    await state.set_state(SetAdmin.admin_id)


@router.callback_query(F.data == "addadmin")
async def add_admin(callback: CallbackQuery, state: FSMContext):
    try:
        file_path = f"data/costumers_{datetime.now().strftime("%d-%m-%y")}.xlsx"
        export_data_to_excel(session, 'costumers', file_path)
        document = FSInputFile(file_path)
        logger.info(f"Выгрузка для {callback.from_user.id} данных из таблицы costumers успешно")
    except Exception as e:
        logger.exception(f"Ошибка при выгрузке данных из таблицы costumers для {callback.from_user.id}: {e}")
        return
    await callback.message.answer_document(document=document, caption=f"Выгрузка данных из таблицы costumers")
    os.remove(file_path)
    await callback.message.answer("Введите ID админа:")
    await state.update_data(action='add')
    await state.set_state(SetAdmin.admin_id)


@router.message(SetAdmin.admin_id)
async def set_admin_id(message: Message, state: FSMContext):
    try:
        admin_id = int(message.text)
        logger.info("Успешное преобразования ай ди админа в set_admin_id(")
    except Exception as e:
        logger.exception(f"Ошибка преобразования ай ди админа в set_admin_id(: {e}")
        await message.answer("Введен не верный ай ди админа, попробуйте еще раз")
        return
    data = await state.get_data()
    my_action = data['action']
    if my_action == 'delete':
        set_admin(session, admin_id, to_delete=True)
        await message.answer("Админ удален")
    elif my_action == 'add':
        set_admin(session, admin_id, to_delete=False)
        await message.answer("Админ добавлен")
    await state.clear()
