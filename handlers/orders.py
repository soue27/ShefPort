from aiogram import Router, F, Bot, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from data.config import SUPERADMIN_ID
from database.db import (session, Order, get_product_by_id, get_active_entity,
                         set_active_entity, save_product_to_entity, get_entity_items,
                         change_item_quantity, delete_entity_item, confirm_entity, get_entity_item, get_all_admin,
                         delete_entity, get_entity_by_id)
from database.models import OrderItems, Product
from keyboards.carts_kb import item_action_kb, cart_main_kb, delete_confirm_kb


router = Router(name='orders')

user_order_messages = {}


class Orderitemscount(StatesGroup):
    Orderitemscount = State()


@router.callback_query(F.data.startswith('add_to_order_'))
async def add_product_to_order(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки добавления товара в корзину"""
    product_id = int(callback.data.split("_")[3])
    product: Product = get_product_by_id(session, product_id)
    print(get_active_entity(session, callback.from_user.id, Order))
    if not get_active_entity(session, callback.from_user.id, Order):
         order = set_active_entity(session, callback.from_user.id, Order)
    order = get_active_entity(session, callback.from_user.id, Order)
    await state.update_data(product_id=product_id,
                            user_id=callback.from_user.id,
                            price=product.price,
                            name=product.name,
                            order_id=order.id,
    )
    if product.unit in ["кг", "кг."]:
        text = f"Пожалуйста, введите количество товара: <b>{product.name}</b> для заказа\n" \
               f"'Обратите внимание товар весовой'"
    else:
        text = f"Пожалуйста, введите количество товара: <b>{product.name}</b> для заказа\n"
    await callback.message.answer(text=text)
    await state.set_state(Orderitemscount.Orderitemscount)
    await callback.answer()


@router.message(Orderitemscount.Orderitemscount)
async def get_orderitems_count(message: Message, state: FSMContext):
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
                            entity_id=data['order_id'],
                            product_id=data['product_id'],
                            quantity=data['count'],
                            unit_price=data['price'],
                            model=OrderItems
                            ):
        await message.answer(text="Товар добавлен в заказ", show_alert=True)
    await state.clear()

@router.message(F.text == "🛍  Мои заказы")
async def show_order(message: Message):
    """Показ корзины"""

    order = get_active_entity(session, message.from_user.id, Order)
    if not order or not order.items:
        await message.answer("Ваш заказ пуст, выберите товары для добавления")
        return
    items = get_entity_items(session, order.id, OrderItems)

    # Сохранение списка сообщений пользователя
    user_order_messages[message.from_user.id] = []

    # Вывод всех товаров как отдельные сообщения
    for item in items:
        text = (
            f"🛍 <b>{item.product.name}</b>\n"
            f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
            f"Стоимость: <b>{item.total_price:.2f} ₽</b>"
        )
        msg = await message.answer(
            text,
            reply_markup=item_action_kb(item.id, "OrderItem"),
            parse_mode=ParseMode.HTML
        )
        user_order_messages[message.from_user.id].append(msg.message_id)

    # Итоговая кнопка
    final_msg = await message.answer(
        f"Итого: *{order.total_amount:.2f}*₽",
        reply_markup=cart_main_kb(order.id, "Order"),
        parse_mode="Markdown"
    )
    user_order_messages[message.from_user.id].append(final_msg.message_id)


# -------------------------------------------------------
#               Кнопки + и -
# -------------------------------------------------------

@router.callback_query(F.data.startswith("OrderItem_plus"))
async def plus_orderitem(call: CallbackQuery):
    _, item_id = call.data.split(":")

    item = change_item_quantity(session, int(item_id), +1, OrderItems)

    await call.message.edit_text(
        f"🛍 <b>{item.product.name}</b>\n"
        f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
        f"Стоимость: <b>{item.total_price:.2f} ₽</b>",
        reply_markup=item_action_kb(item.id, "OrderItem"),
        parse_mode=ParseMode.HTML
    )
    await call.answer()


@router.callback_query(F.data.startswith("OrderItem_minus"))
async def minus_orderitem(call: CallbackQuery):
    _, item_id = call.data.split(":")

    item = change_item_quantity(session, int(item_id), -1, OrderItems)

    await call.message.edit_text(
        f"🛍 <b>{item.product.name}</b>\n"
        f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
        f"Стоимость: <b>{item.total_price:.2f} ₽</b>",
        reply_markup=item_action_kb(item.id, "OrderItem"),
        parse_mode=ParseMode.HTML
    )
    await call.answer()


# -------------------------------------------------------
#                  Удаление товара
# -------------------------------------------------------

@router.callback_query(F.data.startswith("OrderItem_delete:"))
async def delete_orderitem_request(call: CallbackQuery):
    _, item_id = call.data.split(":")
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(item_id), "OrderItem"))
    await call.answer()


@router.callback_query(F.data.startswith("OrderItem_delete_confirm:"))
async def delete_orderitem_confirm(call: CallbackQuery):
    _, item_id = call.data.split(":")

    delete_entity_item(session, int(item_id), OrderItems)

    await call.message.edit_text("🗑 Товар удалён")
    await call.answer()


@router.callback_query(F.data.startswith("OrderItem_delete_cancel:"))
async def delete_orderitem_cancel(call: CallbackQuery):
    _, item_id = call.data.split(":")
    item = get_entity_item(session, int(item_id), OrderItems)
    await call.message.edit_text(
        f"🛒 <b>{item.product.name}</b>\n"
        f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
        f"Стоимость: <b>{item.total_price:.2f} ₽</b>",
        reply_markup=item_action_kb(item.id, "OrderItem"),
        parse_mode=ParseMode.HTML
    )
    await call.answer(text="Удаление отменено ❌", show_alert=False)


# -------------------------------------------------------
#             Подтверждение корзины
# -------------------------------------------------------

@router.callback_query(F.data.startswith("Order_confirm"))
async def confirm_order_handler(call: CallbackQuery):
    _,order_id = call.data.split(":")
    order = confirm_entity(session, int(order_id), Order)
    await call.message.answer(
        f"✅ Ваш заказ принят!\n"
        f"Номер заказа: {order.id}\n"
        f"Всего позиций: {int(order.total_items)}\n"
        f"Мы направим Вам информацию о готовности."
    )

    # Удаляем все сообщения корзины
    user_id = call.from_user.id
    if user_id in user_order_messages:
        for mid in user_order_messages[user_id]:
            try:
                await call.bot.delete_message(user_id, mid)
            except:
                pass
        del user_order_messages[user_id]
        # Уведомление админам
    admins = get_all_admin(session)
    for admin in admins:
        await call.bot.send_message(chat_id=admin, text=f"{call.from_user.full_name} собрал заказ \n"
                                                            f" №: {order.id}, всего {int (order.total_items)} позиций")
    await call.answer()


# -------------------------------------------------------
#             Удаление заказа
# -------------------------------------------------------
@router.callback_query(F.data.startswith("Order_delete:"))
async def confirm_order_handler(call: CallbackQuery):
    """Delete Cart"""
    _,order_id = call.data.split(":")
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(order_id), "Order"))
    await call.answer()


@router.callback_query(F.data.startswith("Order_delete_confirm:"))
async def delete_orderitem_confirm(call: CallbackQuery):
    _, item_id = call.data.split(":")

    delete_entity(session, int(item_id), Order)

    await call.message.edit_text("🗑 Заказ удалён")
    await call.answer()


@router.callback_query(F.data.startswith("Order_delete_cancel:"))
async def delete_order_cancel(call: CallbackQuery):
    """Обработка отмены корзины и перерисовка сообщения"""
    _, item_id = call.data.split(":")
    print(item_id)
    item = get_entity_by_id(session, int(item_id), Order)
    await call.message.edit_text(
        f"Итого: *{item.total_amount:.2f}*₽",
        reply_markup=cart_main_kb(item.id, "Cart"),
        parse_mode="Markdown"
    )
    await call.answer(text="Удаление отменено ❌", show_alert=False)
# -------------------------------------------------------
#                Очистка экрана
# -------------------------------------------------------

@router.callback_query(F.data =="Order_cleanup")
async def cleanup_ordermessages(call: CallbackQuery):
    user_id = call.from_user.id

    if user_id in user_order_messages:
        for mid in user_order_messages[user_id]:
            try:
                await call.bot.delete_message(user_id, mid)
            except:
                pass
        del user_order_messages[user_id]

    await call.answer("Экран очищен")