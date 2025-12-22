import os


from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from loguru import logger
from sqlalchemy.util import await_only

from database.db import session, get_product_by_article, entity_to_excel, delete_product_by_id
from database.models import Product
from keyboards.admin_kb import get_product_change_kb, get_product_delete_kb, get_edit_product_kb

router = Router(name='admin_product')


user_messages = {}


class ViewProduct(StatesGroup):
    article = State()


@router.callback_query(F.data == "view_product")
async def get_product_article(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажати кнопки 'просмотр товара
    :param
        callback
        state
    """
    user_messages[callback.from_user.id] = []
    msg = await callback.message.answer("Введите артикул товара:")
    user_messages[callback.from_user.id].append(msg.message_id)
    await state.set_state(ViewProduct.article)


@router.message(ViewProduct.article)
async def view_product(message: Message, state: FSMContext):
    """Обработчик ввода артикула товара, поиск товара в БД и отправка юзеру"""
    article = message.text
    user_messages[message.from_user.id].append(message.message_id)
    try:
        tovar = get_product_by_article(session, article)
        await state.update_data(tovar=tovar)
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
        msg = await message.answer_document(FSInputFile(file_name))
        user_messages[message.from_user.id].append(msg.message_id)
        text = (f"Артикль: <b>{tovar.article}</b>\n"
                             f"Название: <b>{tovar.name}</b>\n"
                             f"Цена: <b>{tovar.price}</b>\n"
                             f"Единицы: <b>{tovar.unit}</b>\n"
                             f"Остаток: <b>{tovar.ostatok}</b>\n"
                             f"Описание: <b>{tovar.description}</b>\n"
                             f"Фото: <b>{tovar.main_image}</b>\n")
        msg = await message.answer(text=text, reply_markup=get_product_change_kb(tovar.id, tovar.article))
        user_messages[message.from_user.id].append(msg.message_id)
        print(tovar.id)
        logger.info(f"Товар {article} загружен в файл для {message.from_user.id}")
        os.remove(file_name)
    except Exception as e:
        logger.error(f"Ошибка при загрузке товара {article} для {message.from_user.id}: {e}")
    finally:
        await state.clear()


@router.callback_query(F.data.startswith("delete_"))
async def delete_product(callback: CallbackQuery):
    """Функция обработки нажатия кнопки удаления товара"""
    try:
        product_id = int(callback.data.split("_")[1])
        logger.info("Успешное преобразования ай ди товара в delete_product")
    except Exception as e:
        logger.exception(f"Ошибка преобразования ай ди товара в delete_product: {e}")
        await callback.message.answer("Возникла ошибка, попробуйте еще раз")
        return
    try:
        product = session.get(Product, product_id)
        logger.info(f"Успешно выполнен запрос session.get в delete_product")
    except Exception as e:
        logger.exception(f"Не успешно выполнен запрос session.get в delete_product: {e}")
        await callback.message.answer("Возникла ошибка, попробуйте еще раз")
        return
    msg = await callback.message.answer(f"Подтвердите удаление товара '{product.name}', артикул №{product.article}",
                                  reply_markup=get_product_delete_kb(product_id))
    user_messages[callback.from_user.id].append(msg.message_id)



@router.callback_query(F.data.startswith("deleteconfirm_"))
async def confirm_delete_product(callback: CallbackQuery):
    """Обратка подтверждения для удаления товара"""
    try:
        product_id = int(callback.data.split("_")[1])
        logger.info("Успешное преобразования ай ди товара в confirm_delete_product")
    except Exception as e:
        logger.exception(f"Ошибка преобразования ай ди товара в confirm_delete_product: {e}")
        await callback.message.answer("Возникла ошибка, попробуйте еще раз")
        return
    if delete_product_by_id(session, product_id):
        await callback.message.answer(f"✅ Товар удален")
        logger.info(f"Успешное удаление товара {product_id} в confirm_delete_product")
        user_id = callback.from_user.id
        if user_id in user_messages:
            for mid in user_messages[user_id]:
                try:
                    await callback.bot.delete_message(user_id, mid)
                except Exception as e:
                    logger.exception(f"Ошибка при удалении сообщений в confirm_delete_product: {e}")
            del user_messages[user_id]
    else:
        await callback.answer("❌ Товар не найден", show_alert=True)
        logger.error(f"Неуспешное удаление товара {product_id} в confirm_delete_product")


@router.callback_query(F.data.startswith("deleteback"))
async def confirm_back_product(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("❌ Отмена удаления товара")
    user_id = callback.from_user.id
    if user_id in user_messages:
        for mid in user_messages[user_id]:
            try:
                await callback.bot.delete_message(user_id, mid)
            except Exception as e:
                logger.exception(f"Ошибка при удалении сообщений confirm_back_product: {e}")
        del user_messages[user_id]
    logger.info(f"Отмена удаления товара в confirm_delete_product")


@router.callback_query(F.data.startswith("confirmedit_"))
async def show_edit_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    await callback.message.edit_text("Выберите, что будем менять", reply_markup=get_edit_product_kb(product_id))

