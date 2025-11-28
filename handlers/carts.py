import asyncio

from aiogram import Router, F, types
from aiogram.client import bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from database.db import (
    session, get_product_by_id, set_active_entity, get_active_entity,
    save_product_to_entity, get_entity_items, delete_entity_item, confirm_entity, change_item_quantity, get_all_admin,
    delete_entity, get_entity_item, get_entity_by_id
)
from database.models import Product, Cart, CartItems
from keyboards.carts_kb import item_action_kb, delete_confirm_kb, cart_main_kb

router = Router(name="carts")

# Храним список сообщений, чтобы потом удалить
user_cart_messages = {}


class Itemscount(StatesGroup):
    itemscount = State()


# @router.message(F.text == '🛒 Моя корзина')
# async def show_carts(message: Message):
#     """Обработчик нажатия кнопки Моя корзина"""
#     nomer = get_active_cart(session, message.from_user.id)
#     if not nomer:
#         await message.answer(text="Ваша корзина пуста, выберите товары", show_alert=True)
#     else:
#         await message.answer(text=f"В вашей корзине есть товары, в путь Корзина №{nomer}", show_alert=True)


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_product_to_cart(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки добавления товара в корзину"""
    product_id = int(callback.data.split("_")[3])
    product: Product = get_product_by_id(session, product_id)
    await state.update_data(product_id=product_id,
                            user_id=callback.from_user.id,
                            price=product.price,
                            name=product.name,
                            )
    if not get_active_entity(session, callback.from_user.id, Cart):
         cart = set_active_entity(session, callback.from_user.id, Cart)
    cart = get_active_entity(session, callback.from_user.id, Cart)
    await state.update_data(cart_id=cart.id)
    if product.unit in ["кг", "кг."]:
        text = f"Пожалуйста, введите количество товара: <b>{product.name}</b> для покупки\n" \
               f"'Обратите внимание товар весовой'"
    else:
        text = f"Пожалуйста, введите количество товара: <b>{product.name}</b> для покупки\n"
    await callback.message.answer(text=text)
    await state.set_state(Itemscount.itemscount)
    await callback.answer()


@router.message(Itemscount.itemscount)
async def get_items_count(message: Message, state: FSMContext):
    """обработка ввода количества товара в стейте"""
    user_input = message.text.replace(',', '.') if ',' in message.text else message.text
    try:
        count = float(user_input.strip())
    except ValueError:
        await message.answer(text="Введите корректное количество товара")
        return
    if count <= 0:
        await message.answer(text="Введите корректное количество товара")
        return
    await state.update_data(count=count)
    data = await state.get_data()
    if save_product_to_entity(session=session,
                            entity_id=data['cart_id'],
                            product_id=data['product_id'],
                            quantity=data['count'],
                            unit_price=data['price'],
                            model=CartItems
                            ):
        await message.answer(text="Товар добавлен в корзину", show_alert=True)
    await state.clear()


@router.message(F.text == "🛒 Моя корзина")
async def show_carts(message: Message):
    """Показ корзины"""

    cart = get_active_entity(session, message.from_user.id, Cart)
    if not cart or not cart.items:
        await message.answer("Ваша корзина пуста, выберите товары для добавления")
        return
    items = get_entity_items(session, cart.id, CartItems)
    # Сохранение списка сообщений пользователя
    user_cart_messages[message.from_user.id] = []

    # Вывод всех товаров как отдельные сообщения
    for item in items:
        text = (
            f"🛒 <b>{item.product.name}</b>\n"
            f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
            f"Стоимость: <b>{item.total_price:.2f} ₽</b>"
        )
        msg = await message.answer(
            text,
            reply_markup=item_action_kb(item.id, "CartItem"),
            parse_mode=ParseMode.HTML
        )
        user_cart_messages[message.from_user.id].append(msg.message_id)

    # Итоговая кнопка
    final_msg = await message.answer(
        f"Итого: *{cart.total_amount:.2f}*₽",
        reply_markup=cart_main_kb(cart.id, "Cart"),
        parse_mode="Markdown"
    )
    user_cart_messages[message.from_user.id].append(final_msg.message_id)


# -------------------------------------------------------
#               Кнопки + и -
# -------------------------------------------------------

@router.callback_query(F.data.startswith("CartItem_plus"))
async def plus_item(call: CallbackQuery):
    _, item_id = call.data.split(":")

    item = change_item_quantity(session, int(item_id), +1, CartItems)

    await call.message.edit_text(
        f"🛒 <b>{item.product.name}</b>\n"
        f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
        f"Стоимость: <b>{item.total_price:.2f} ₽</b>",
        reply_markup=item_action_kb(item.id, "CartItem"),
        parse_mode=ParseMode.HTML
    )
    await call.answer()


@router.callback_query(F.data.startswith("CartItem_minus"))
async def minus_item(call: CallbackQuery):
    _, item_id = call.data.split(":")

    item = change_item_quantity(session, int(item_id), -1, CartItems)

    await call.message.edit_text(
        f"🛒 <b>{item.product.name}</b>\n"
        f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
        f"Стоимость: <b>{item.total_price:.2f} ₽</b>",
        reply_markup=item_action_kb(item.id, "CartItem"),
        parse_mode=ParseMode.HTML
    )
    await call.answer()


# -------------------------------------------------------
#                  Удаление товара
# -------------------------------------------------------

@router.callback_query(F.data.startswith("CartItem_delete:"))
async def delete_item_request(call: CallbackQuery):
    _, item_id = call.data.split(":")
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(item_id), "CartItem"))
    await call.answer()


@router.callback_query(F.data.startswith("CartItem_delete_confirm:"))
async def delete_item_confirm(call: CallbackQuery):
    _, item_id = call.data.split(":")

    delete_entity_item(session, int(item_id), CartItems)

    await call.message.edit_text("🗑 Товар удалён")
    await call.answer()


@router.callback_query(F.data.startswith("CartItem_delete_cancel:"))
async def delete_item_cancel(call: CallbackQuery):
    """Обработка отмены удаления товара из корзины и перерисовка сообщения"""
    _, item_id = call.data.split(":")
    item = get_entity_item(session, int(item_id), CartItems)
    await call.message.edit_text(
        f"🛒 <b>{item.product.name}</b>\n"
        f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
        f"Стоимость: <b>{item.total_price:.2f} ₽</b>",
        reply_markup=item_action_kb(item.id, "CartItem"),
        parse_mode=ParseMode.HTML
    )
    await call.answer(text="Удаление отменено ❌", show_alert=False)


# -------------------------------------------------------
#             Подтверждение корзины
# -------------------------------------------------------

@router.callback_query(F.data.startswith("Cart_confirm"))
async def confirm_cart_handler(call: CallbackQuery):
    _, cart_id = call.data.split(":")

    cart = confirm_entity(session, int(cart_id), Cart)
    # await call.message.edit_text("✅ Ваш заказ принят. Мы направим Вам информацию о готовности")
    # await asyncio.sleep(2)
    await call.message.answer(
        f"✅ Ваш заказ принят!\n"
        f"Номер заказа: {cart.id}\n"
        f"Всего позиций: {int(cart.total_items)}\n"
        f"Мы направим Вам информацию о готовности."
    )
    # Удаляем все сообщения корзины
    user_id = call.from_user.id
    if user_id in user_cart_messages:
        for mid in user_cart_messages[user_id]:
            try:
                await call.bot.delete_message(user_id, mid)
            except:
                pass
        del user_cart_messages[user_id]
    # Уведомление админам
    admins = get_all_admin(session)
    for admin in admins:
        await call.bot.send_message(chat_id=admin, text=f"{call.from_user.full_name} собрал заказ \n"
                                                        f" №: {cart.id}, всего {int (cart.total_items)} позиций")
    await call.answer()

# -------------------------------------------------------
#             Удаление корзины
# -------------------------------------------------------
@router.callback_query(F.data.startswith("Cart_delete:"))
async def confirm_cart_handler(call: CallbackQuery):
    """Delete Cart"""
    _, cart_id = call.data.split(":")
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(cart_id), "Cart"))
    await call.answer()


@router.callback_query(F.data.startswith("Cart_delete_confirm:"))
async def delete_item_confirm(call: CallbackQuery):
    _, item_id = call.data.split(":")

    delete_entity(session, int(item_id), Cart)

    await call.message.edit_text("🗑 Заказ удалён")
    await call.answer()


@router.callback_query(F.data.startswith("Cart_delete_cancel:"))
async def delete_cancel(call: CallbackQuery):
    """Обработка отмены корзины и перерисовка сообщения"""
    print(user_cart_messages)
    _, item_id = call.data.split(":")
    print(item_id)
    item = get_entity_by_id(session, int(item_id), Cart)
    print(item)
    await call.message.edit_text(
        f"Итого: *{item.total_amount:.2f}*₽",
        reply_markup=cart_main_kb(item.id, "Cart"),
        parse_mode="Markdown"
    )
    await call.answer(text="Удаление отменено ❌", show_alert=False)





# -------------------------------------------------------
#                Очистка экрана
# -------------------------------------------------------

@router.callback_query(F.data == "Cart_cleanup")
async def cleanup_messages(call: CallbackQuery):
    user_id = call.from_user.id

    if user_id in user_cart_messages:
        for mid in user_cart_messages[user_id]:
            try:
                await call.bot.delete_message(user_id, mid)
            except:
                pass
        del user_cart_messages[user_id]

    await call.answer("Экран очищен")

