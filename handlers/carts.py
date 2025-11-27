from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from database.db import (
    session, get_product_by_id, set_active_entity, get_active_entity,
    save_product_to_entity, get_entity_items, delete_entity_item, confirm_entity, change_item_quantity
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
    if not get_active_entity(session, callback.from_user.id, Cart):
         cart = set_active_entity(session, callback.from_user.id, Cart)
    cart = get_active_entity(session, callback.from_user.id, Cart)
    await state.update_data(product_id=product_id,
                            user_id=callback.from_user.id,
                            price=product.price,
                            name=product.name,
                            cart_id=cart.id,
    )
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
    print(data)
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
    if not cart:
        await message.answer("Ваша корзина пуста, выберите товары для добавления")
        return
    print(cart, type(cart))
    items = get_entity_items(session, cart.id, CartItems)

    # Сохранение списка сообщений пользователя
    user_cart_messages[message.from_user.id] = []

    # Вывод всех товаров как отдельные сообщения
    for item in items:
        text = (
            f"🛒 *{item.product.name}*\n"
            f"Количество: *{item.quantity}* {item.product.unit}\n"
            f"Стоимость: *{item.total_price:.2f}*₽"
        )
        msg = await message.answer(
            text,
            reply_markup=item_action_kb(item.id, "cart"),
            parse_mode="Markdown"
        )
        user_cart_messages[message.from_user.id].append(msg.message_id)

    # Итоговая кнопка
    final_msg = await message.answer(
        f"Итого: *{cart.total_amount:.2f}*₽",
        reply_markup=cart_main_kb(cart.id, "cart"),
        parse_mode="Markdown"
    )
    user_cart_messages[message.from_user.id].append(final_msg.message_id)


# -------------------------------------------------------
#               Кнопки + и -
# -------------------------------------------------------

@router.callback_query(F.data.startswith("cart_plus"))
async def plus_item(call: CallbackQuery):
    _, item_id = call.data.split(":")

    item = change_item_quantity(session, int(item_id), +1, CartItems)

    await call.message.edit_text(
        f"🛒 *{item.product.name}*\n"
        f"Количество: *{item.quantity}* {item.product.unit}\n"
        f"Стоимость: *{item.total_price:.2f}*₽",
        reply_markup=item_action_kb(item.id, "cart"),
        parse_mode="Markdown"
    )
    await call.answer()


@router.callback_query(F.data.startswith("cart_minus"))
async def minus_item(call: CallbackQuery):
    _, item_id = call.data.split(":")

    item = change_item_quantity(session, int(item_id), -1, CartItems)

    await call.message.edit_text(
        f"🛒 *{item.product.name}*\n"
        f"Количество: *{item.quantity}* {item.product.unit}\n"
        f"Стоимость: *{item.total_price:.2f}*₽",
        reply_markup=item_action_kb(item.id, "cart"),
        parse_mode="Markdown"
    )
    await call.answer()


# -------------------------------------------------------
#                  Удаление товара
# -------------------------------------------------------

@router.callback_query(F.data.startswith("cart_delete:"))
async def delete_item_request(call: CallbackQuery):
    _, item_id = call.data.split(":")
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(item_id), "cart"))
    await call.answer()


@router.callback_query(F.data.startswith("cart_delete_confirm:"))
async def delete_item_confirm(call: CallbackQuery):
    _, item_id = call.data.split(":")

    delete_entity_item(session, int(item_id), CartItems)

    await call.message.edit_text("🗑 Товар удалён")
    await call.answer()


@router.callback_query(F.data.startswith("cart_delete_cancel"))
async def delete_item_cancel(call: CallbackQuery):
    await call.message.edit_text("Отменено")
    await call.answer()


# -------------------------------------------------------
#             Подтверждение корзины
# -------------------------------------------------------

@router.callback_query(F.data.startswith("cart_confirm"))
async def confirm_cart_handler(call: CallbackQuery):
    _, cart_id = call.data.split(":")

    confirm_entity(session, int(cart_id), Cart)

    await call.message.edit_text("✅ Заказ подтверждён")

    # Удаляем все сообщения корзины
    user_id = call.from_user.id
    if user_id in user_cart_messages:
        for mid in user_cart_messages[user_id]:
            try:
                await call.bot.delete_message(user_id, mid)
            except:
                pass
        del user_cart_messages[user_id]

    await call.answer()


# -------------------------------------------------------
#                Очистка экрана
# -------------------------------------------------------

@router.callback_query(F.data == "cart_cleanup")
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

