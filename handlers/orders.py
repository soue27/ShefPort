from typing import Sequence, Any

from aiogram import Router, F, Bot, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from database.db import (
    session,
    get_product_by_id,
    get_active_entity,
    set_active_entity,
    save_product_to_entity,
    get_entity_items,
    change_item_quantity,
    delete_entity_item,
    confirm_entity,
    get_entity_item,
    get_all_admin,
    delete_entity,
    get_entity_by_id,
    get_costumer_id,
    get_entity_by_user_id,
    get_all_categories, get_entity_id_by_items_id,
)
from database.models import OrderItems, Product, Order, DeliveryMode
from handlers.costumer import delivery_message
from keyboards.carts_kb import (
    item_action_kb,
    cart_main_kb,
    delete_confirm_kb,
    previous_cart_kb,
    previous_cartlist_kb,
    back_kb,
)
from keyboards.categorieskb import get_categories_kb, show_in_stock_kb

router = Router(name='orders')

user_order_messages = {}


def commit_session(session):
    """Коммитим изменения с обработкой ошибок и откатом при исключении."""
    try:
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(f"Ошибка при коммите сессии: {e}")
        raise

class Orderitemscount(StatesGroup):
    Orderitemscount = State()


@router.callback_query(F.data.startswith('add_to_order_'))
async def add_product_to_order(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки добавления товара в корзину"""
    try:
        product_id = int(callback.data.split("_")[3])
    except Exception as e:
        logger.exception(
            f" Ошибка преобразования ай ди продукта в 'add_product_to_order': {e}"
        )
        return
    try:
        product: Product = get_product_by_id(session, product_id)
        logger.info(
            f"'add_product_to_order': Админ {callback.from_user.id} получил данные 'get_product_by_id' {product_id} "
        )
    except Exception as e:
        logger.exception(
                f" Запрос пользователя {callback.from_user.id} в БД 'get_product_by_id', номер товара {product_id}' "
                f"  в 'add_product_to_order' выполнен неуспешно: {e}"
        )
        return
    try:
        order = get_active_entity(session, callback.from_user.id, Order)
        logger.info(
            f"'add_product_to_order': Админ {callback.from_user.id} получил данные 'get_active_entity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_active_entity', номер товара {product_id}' "
            f"  в 'add_product_to_order' выполнен неуспешно: {e}"
        )
        return
    await state.update_data(product_id=product_id,
                            user_id=callback.from_user.id,
                            price=product.price,
                            name=product.name,
    )
    if not order:
        order = set_active_entity(session, callback.from_user.id, Order)

        commit_session(session)
    try:
        order = get_active_entity(session, callback.from_user.id, Order)
        logger.info(
            f"'add_product_to_order': Админ {callback.from_user.id} получил данные 'get_active_entity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_active_entity', номер товара {product_id}' "
            f"  в 'add_product_to_order' выполнен неуспешно: {e}"
        )
        return

    await state.update_data(order_id=order.id)
    if product.unit in ["кг", "кг."]:
        text = f"Пожалуйста, введите количество товара: <b>{product.name}</b> для заказа\n" \
               f"'Обратите внимание товар весовой'"
    else:
        text = f"Пожалуйста, введите количество товара: <b>{product.name}</b> для заказа\n"
    await callback.message.answer(text=text)
    logger.info(f"'add_product_to_order': Пользователь {callback.from_user.id} "
                f"перешел в состояний Orderitemscount.Orderitemscount для {product.id}"
    )
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
    try:
        if save_product_to_entity(session=session,
                                entity_id=data['order_id'],
                                product_id=data['product_id'],
                                quantity=data['count'],
                                unit_price=data['price'],
                                model=OrderItems
                                ):
            await message.answer(text="Товар добавлен в заказ", show_alert=True)
        commit_session(session)
        logger.info(
            f"Пользователь {message.from_user.id} сохранил товар {data['product_id']} в заказ {data['order_id']}"
            f" количество {data['count']} запрос 'save_product_to_entity' get_orderitems_count")
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {message.from_user.id} в БД 'save_product_to_entity', номер заказа {data['order_id']}' "
            f"  в 'get_orderitems_count' выполнен неуспешно: {e}"
        )
    await state.clear()


@router.message(F.text == "🛍  Мои заказы")
async def show_order(message: Message):
    """Показ корзины"""
    try:
        order = get_active_entity(session, message.from_user.id, Order)
        logger.info(
            f"'show_order':  {message.from_user.id} получил данные 'get_active_entity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {message.from_user.id} в БД 'get_active_entity', номер корзины {order.id}' "
            f"  в 'show_order' выполнен неуспешно: {e}"
        )
        return
    if not order or not order.items:
        await message.answer(
            "Ваша корзина пуста, выберите товары для добавления в каталоге, \n"
            "либо нажмите 👇 для просмотра Ваших заказов",
            reply_markup=previous_cart_kb("Order"),
        )
        return
    try:
        items = get_entity_items(session, order.id, OrderItems)
        logger.info(
            f"'show_order':  {message.from_user.id} получил данные 'get_entity_items' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {message.from_user.id} в БД 'get_entity_items', номер корзины {order.id}' "
            f"  в 'show_order' выполнен неуспешно: {e}"
        )
        return
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
async def plus_orderitem(call: CallbackQuery, bot: Bot):
    """Обработка нажатия кнопки увеличения товара в заказе"""
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'plus_orderitem' выполнен неуспешно: {e}"
        )
        return
    try:
        item = change_item_quantity(session, item_id, +1, OrderItems)
        logger.info(
            f"'plus_orderitem':  {call.from_user.id} получил данные 'change_item_quantity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'change_item_quantity', номер товара {item_id}' "
            f"  в 'plus_orderitem' выполнен неуспешно: {e}"
        )
        return
    await call.message.edit_text(
        f"🛍 <b>{item.product.name}</b>\n"
        f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
        f"Стоимость: <b>{item.total_price:.2f} ₽</b>",
        reply_markup=item_action_kb(item.id, "OrderItem"),
        parse_mode=ParseMode.HTML
    )
    await call.answer()
    # Перерисовка итоговой стоимости корзины
    key = list(user_order_messages.keys())[0]
    message_id = user_order_messages[key][-1]
    order_id = get_entity_id_by_items_id(session, item_id, OrderItems)
    order = get_entity_by_id(session, order_id, Order)
    await bot.edit_message_text(
        f"Итого: *{order.total_amount:.2f}*₽",
        chat_id=key,
        message_id=message_id,
        reply_markup=cart_main_kb(order.id, "Order"),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("OrderItem_minus"))
async def minus_orderitem(call: CallbackQuery, bot: Bot):
    """Обработка нажатия кнопки уменьшения товара в заказе"""
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'minus_orderitem' выполнен неуспешно: {e}"
        )
        return
    try:
        item = change_item_quantity(session, item_id, -1, OrderItems)
        logger.info(
            f"'minus_orderitem':  {call.from_user.id} получил данные 'change_item_quantity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'change_item_quantity', номер товара {item_id}' "
            f"  в 'minus_orderitem' выполнен неуспешно: {e}"
        )
        return

    await call.message.edit_text(
        f"🛍 <b>{item.product.name}</b>\n"
        f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
        f"Стоимость: <b>{item.total_price:.2f} ₽</b>",
        reply_markup=item_action_kb(item.id, "OrderItem"),
        parse_mode=ParseMode.HTML
    )
    await call.answer()
    # Перерисовка итоговой стоимости корзины
    key = list(user_order_messages.keys())[0]
    message_id = user_order_messages[key][-1]
    order_id = get_entity_id_by_items_id(session, item_id, OrderItems)
    order = get_entity_by_id(session, order_id, Order)
    await bot.edit_message_text(
        f"Итого: *{order.total_amount:.2f}*₽",
        chat_id=key,
        message_id=message_id,
        reply_markup=cart_main_kb(order.id, "Order"),
        parse_mode="Markdown"
    )


# -------------------------------------------------------
#                  Удаление товара
# -------------------------------------------------------

@router.callback_query(F.data.startswith("OrderItem_delete:"))
async def delete_orderitem_request(call: CallbackQuery):
    """Обработка кнопки удаления товара в корзине, с запросом подтверждения"""
    _, item_id = call.data.split(":")
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(item_id), "OrderItem"))
    await call.answer()


@router.callback_query(F.data.startswith("OrderItem_delete_confirm:"))
async def delete_orderitem_confirm(call: CallbackQuery, bot: Bot):
    """Обработка подтверждения удаления товара в корзине и удаление из БД"""
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
        order_id = get_entity_id_by_items_id(session, item_id, OrderItems)
        order = get_entity_by_id(session, order_id, Order)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'delete_orderitem_confirm' выполнен неуспешно: {e}"
        )
        return
    try:
        delete_entity_item(session, item_id, OrderItems)
        commit_session(session)
        logger.info(
            f"'delete_orderitem_confirm':  {call.from_user.id} получил данные 'delete_entity_item' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'delete_entity_item', номер товара {item_id}' "
            f"  в 'delete_orderitem_confirm' выполнен неуспешно: {e}"
        )
        return
    await call.message.edit_text("🗑 Товар удалён")
    await call.answer()
    # Перерисовка итоговой стоимости корзины
    key = list(user_order_messages.keys())[0]
    message_id = user_order_messages[key][-1]
    await bot.edit_message_text(
        f"Итого: *{order.total_amount:.2f}*₽",
        chat_id=key,
        message_id=message_id,
        reply_markup=cart_main_kb(order.id, "Order"),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("OrderItem_delete_cancel:"))
async def delete_orderitem_cancel(call: CallbackQuery):
    """Обработка отмены удаления товара из корзины и перерисовка сообщения"""
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'delete_item_confirm' выполнен неуспешно: {e}"
        )
        return
    try:
        item = get_entity_item(session, item_id, OrderItems)
        logger.info(
            f"'delete_orderitem_cancel':  {call.from_user.id} получил данные 'get_entity_item' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'get_entity_item', номер товара {item_id}' "
            f"  в 'delete_orderitem_cancel' выполнен неуспешно: {e}"
        )
        return
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
    try:
        order_id = int(order_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {order_id} в целое "
            f"  в 'confirm_order_handler' выполнен неуспешно: {e}"
        )
        return
    try:
        order = confirm_entity(session, order_id, Order)
        commit_session(session)
        logger.info(
            f"'confirm_order_handler':  {call.from_user.id} получил данные 'confirm_entity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'confirm_entity', номер товара {order_id}' "
            f"  в 'confirm_order_handler' выполнен неуспешно: {e}"
        )
        return
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
    try:
        admins = get_all_admin(session)
        logger.info(
            f"'confirm_order_handler':  {call.from_user.id} получил данные 'get_all_admin' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'get_all_admin' "
            f"  в 'confirm_order_handler' выполнен неуспешно: {e}"
        )
        return
    for admin in admins:
        await call.bot.send_message(chat_id=admin, text=f"{call.from_user.full_name} собрал заказ \n"
                                                            f" №: {order.id}, всего {int (order.total_items)} позиций")
    await call.answer()


# -------------------------------------------------------
#             Удаление заказа
# -------------------------------------------------------
@router.callback_query(F.data.startswith("Order_delete:"))
async def delete_order(call: CallbackQuery):
    """Delete Order"""
    _,order_id = call.data.split(":")
    try:
        order_id = int(order_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {order_id} в целое "
            f"  в 'elete_order' выполнен неуспешно: {e}"
        )
        return
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(order_id), "Order"))
    await call.answer()


@router.callback_query(F.data.startswith("Order_delete_confirm:"))
async def delete_order_confirm(call: CallbackQuery):
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'delete_order_confirm' выполнен неуспешно: {e}"
        )
        return
    try:
        delete_entity(session, int(item_id), Order)
        commit_session(session)
        logger.info(
            f"'delete_order_confirm':  {call.from_user.id} получил данные 'delete_entity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'delete_entity' "
            f"  в 'delete_order_confirm' выполнен неуспешно: {e}"
        )
        return
    await call.message.edit_text("🗑 Заказ удалён")
    await call.answer()


@router.callback_query(F.data.startswith("Order_delete_cancel:"))
async def delete_order_cancel(call: CallbackQuery):
    """Обработка отмены корзины и перерисовка сообщения"""
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'delete_order_cancel' выполнен неуспешно: {e}"
        )
        return
    try:
        item = get_entity_by_id(session, item_id, Order)
        logger.info(
            f"'delete_order_cancel':  {call.from_user.id} получил данные 'get_entity_by_id' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'get_entity_by_id' "
            f"  в 'delete_order_cancel' выполнен неуспешно: {e}"
        )
        return
    await call.message.edit_text(
        f"Итого: *{item.total_amount:.2f}*₽",
        reply_markup=cart_main_kb(item.id, "Order"),
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


# -------------------------------------------------------
#                Показ предыдущих закзазов
# -------------------------------------------------------
@router.callback_query(F.data == "previous_order")
async def show_previus_cart(callback: CallbackQuery):
    user_order_messages[callback.from_user.id] = []
    try:
        user_id = get_costumer_id(session, callback.from_user.id)
        previous_carts: Sequence[Any] = get_entity_by_user_id(session, user_id, Order)
        logger.info(
            f"'show_previus_cart':  {callback.from_user.id} получил данные 'get_costumer_id' и 'get_entity_by_user_id'"
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_costumer_id' or 'get_entity_by_user_id'"
            f"  в 'show_previus_cart' выполнен неуспешно: {e}"
        )
        return
    if not previous_carts: # условие для показа каталога, если не было до этого покупок
        try:
            categories = get_all_categories(session)
            logger.info(
                f"'show_previus_cart'':  {callback.from_user.id} получил данные 'get_all_categories'"
            )
        except Exception as e:
            logger.exception(
                f" Запрос пользователя {callback.from_user.id} в БД 'get_all_categories' "
                f"  в 'show_previus_cart'' выполнен неуспешно: {e}"
            )
            return
        await callback.message.edit_text("У вас не было покупок до настоящего момента, \n"
                                      "выберите товары в нашем каталоге",
                                      reply_markup=show_in_stock_kb())
        await callback.answer()
        return
    else:  # Вывод на экран предыдущих корзин
        await callback.message.edit_text(
            "Список Ваших заказов:",
            reply_markup=previous_cartlist_kb(previous_carts),
        )
        user_order_messages[callback.from_user.id].append(callback.message.message_id)
        await callback.answer()


@router.callback_query(F.data.startswith("previous_cart_"))
async def show_previus_item(callback: CallbackQuery):
    # user_cart_messages[callback.from_user.id] = []
    _, _, cart_id = callback.data.split("_")
    cart_id = int(cart_id)
    try:
        cart_id = int(cart_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} преобразование номера товара {cart_id} в целое "
            f"  в 'delete_cancel' выполнен неуспешно: {e}"
        )
        return
    try:
        items = get_entity_items(session, cart_id, OrderItems)
        logger.info(
            f"'show_previus_item':  {callback.from_user.id} получил данные 'get_entity_items'"
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_entity_items' "
            f"  в 'show_previus_item' выполнен неуспешно: {e}"
        )
        return
    start_msg = await callback.message.answer(text = f"🛒 <b>Заказ №{cart_id}</b>")
    user_id = callback.from_user.id
    if user_id not in user_order_messages:
        user_order_messages[user_id] = []
    user_order_messages[user_id].append(start_msg.message_id)
    for item in items:
        msg = await callback.message.answer(text = f"✅ <b>{item.product.name}</b>\n"
                                            f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
                                            f"Стоимость: <b>{item.total_price:.2f} ₽</b>"
        )
        user_order_messages[user_id].append(msg.message_id)
    back_msg = await callback.message.answer(text="Для возрата к списку заказов нажмите 👇",
                                             reply_markup=back_kb())
    user_order_messages[callback.from_user.id].append(back_msg.message_id)
    if user_id in user_order_messages and user_order_messages[user_id]:
        # Удаляем и возвращаем первый элемент
        user_order_messages[user_id].pop(0)

