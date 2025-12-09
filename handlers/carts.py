from typing import Sequence, Any

from aiogram import Router, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from loguru import logger

from database.db import (
    session,
    get_product_by_id,
    set_active_entity,
    get_active_entity,
    save_product_to_entity,
    get_entity_items,
    delete_entity_item,
    confirm_entity,
    change_item_quantity,
    get_all_admin,
    delete_entity,
    get_entity_item,
    get_entity_by_id,
    get_costumer_id,
    get_entity_by_user_id,
    get_all_categories,
)
from database.models import Product, Cart, CartItems
from keyboards.carts_kb import (
    item_action_kb,
    delete_confirm_kb,
    cart_main_kb,
    previous_cart_kb,
    previous_cartlist_kb,
    back_kb,
)
from keyboards.categorieskb import get_categories_kb

router = Router(name="carts")

# Храним список сообщений, чтобы потом удалить
user_cart_messages = {}


class Itemscount(StatesGroup):
    itemscount = State()


@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_product_to_cart(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки добавления товара в корзину"""
    try:
        product_id = int(callback.data.split("_")[3])
    except Exception as e:
        logger.exception(
            f" Ошибка преобразования ай ди продукта в 'add_product_to_cart': {e}"
        )
        return
    try:
        product: Product = get_product_by_id(session, product_id)
        logger.info(
            f"'add_product_to_cart': Админ {callback.from_user.id} получил данные 'get_product_by_id' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_product_by_id', номер товара {product_id}' "
            f"  в 'add_product_to_cart' выполнен неуспешно: {e}"
        )
        return
    await state.update_data(product_id=product_id,
                            user_id=callback.from_user.id,
                            price=product.price,
                            name=product.name,
                            )
    if not get_active_entity(session, callback.from_user.id, Cart): #Если нет активной корзины, то создаем ее
        cart = set_active_entity(session, callback.from_user.id, Cart)
    try:
        cart = get_active_entity(session, callback.from_user.id, Cart) #Получаем активную корзину
        logger.info(f"'add_product_to_cart': Пользователь {callback.from_user.id} получил активную корзину {cart.id}")
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} в БД 'get_active_entity', номер корзины {cart.id}' "
            f"  в 'add_product_to_cart' выполнен неуспешно: {e}"
        )
        return

    await state.update_data(cart_id=cart.id)
    if product.unit in ["кг", "кг."]:
        text = f"Пожалуйста, введите количество товара: <b>{product.name}</b> для покупки\n" \
               f"'Обратите внимание товар весовой'"
    else:
        text = f"Пожалуйста, введите количество товара: <b>{product.name}</b> для покупки\n"
    await callback.message.answer(text=text)
    logger.info(
        f"'add_product_to_cart': Пользователь {callback.from_user.id} перешел в состояний Itemscount.itemscount для {product.id}"
    )
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
    try:
        if save_product_to_entity(session=session,
                                entity_id=data['cart_id'],
                                product_id=data['product_id'],
                                quantity=data['count'],
                                unit_price=data['price'],
                                model=CartItems
                                ):
            await message.answer(text="Товар добавлен в корзину", show_alert=True)
        logger.info(
            f"Пользователь {message.from_user.id} сохранил товар {data['product_id']} в корзину {data['cart_id']}"
            f" количество {data['count']} запрос 'save_product_to_entity' get_items_count"
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {message.from_user.id} в БД 'save_product_to_entity', номер корзины {data['cart_id']}' "
            f"  в 'get_items_count' выполнен неуспешно: {e}"
        )
    await state.clear()


@router.message(F.text == "🛒 Моя корзина")
async def show_carts(message: Message):
    """Показ корзины пользователя"""
    try:
        cart = get_active_entity(session, message.from_user.id, Cart)
        logger.info(
            f"'show_carts':  {message.from_user.id} получил данные 'get_active_entity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {message.from_user.id} в БД 'get_active_entity', номер корзины {cart.id}' "
            f"  в 'show_carts' выполнен неуспешно: {e}"
        )
        return
    if not cart or not cart.items:
        await message.answer("Ваша корзина пуста, выберите товары для добавления в каталоге, \n"
                             "либо нажмите 👇 для просмотра Ваших заказов",
                             reply_markup=previous_cart_kb())

        return
    try:
        items = get_entity_items(session, cart.id, CartItems)
        logger.info(
            f"'show_carts':  {message.from_user.id} получил данные 'get_entity_items' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {message.from_user.id} в БД 'get_entity_items', номер корзины {cart.id}' "
            f"  в 'show_carts' выполнен неуспешно: {e}"
        )
        return
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
    """Обработка нажатия кнопки увеличения товара в корзине"""
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'plus_item' выполнен неуспешно: {e}"
        )
        return
    try:
        item = change_item_quantity(session, item_id, +1, CartItems)
        logger.info(
            f"'carts.plus_item':  {call.from_user.id} получил данные 'change_item_quantity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'change_item_quantity', номер товара {item_id}' "
            f"  в 'plus_item' выполнен неуспешно: {e}"
        )
        return

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
    """Обработка нажатия кнопки уменьшения товара в корзине"""
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'minus_item' выполнен неуспешно: {e}"
        )
        return
    try:
        item = change_item_quantity(session, item_id, -1, CartItems)
        logger.info(
            f"'carts.minus_item':  {call.from_user.id} получил данные 'change_item_quantity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'change_item_quantity', номер товара {item_id}' "
            f"  в 'minus_item' выполнен неуспешно: {e}"
        )
        return
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
    """Обработка кнопки удаления товара в корзине, с запросом подтверждения"""
    _, item_id = call.data.split(":")
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(item_id), "CartItem"))
    await call.answer()


@router.callback_query(F.data.startswith("CartItem_delete_confirm:"))
async def delete_item_confirm(call: CallbackQuery):
    """Обработка подтверждения удаления товара в корзине и удаление из БД"""
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
        delete_entity_item(session, item_id, CartItems)
        logger.info(
            f"'carts.delete_item_confirm':  {call.from_user.id} получил данные 'delete_entity_item' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'delete_entity_item', номер товара {item_id}' "
            f"  в 'delete_item_confirm' выполнен неуспешно: {e}"
        )
        return
    await call.message.edit_text("🗑 Товар удалён")
    await call.answer()


@router.callback_query(F.data.startswith("CartItem_delete_cancel:"))
async def delete_item_cancel(call: CallbackQuery):
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
        item = get_entity_item(session, item_id, CartItems)
        logger.info(
            f"'carts.delete_item_cancel':  {call.from_user.id} получил данные 'get_entity_item' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'get_entity_item', номер товара {item_id}' "
            f"  в 'delete_item_cancel' выполнен неуспешно: {e}"
        )
        return
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
    try:
        cart_id = int(cart_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {cart_id} в целое "
            f"  в 'delete_item_confirm' выполнен неуспешно: {e}"
        )
        return
    try:
        cart = confirm_entity(session, cart_id, Cart)
        logger.info(
            f"'carts.confirm_cart_handler':  {call.from_user.id} получил данные 'confirm_entity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'confirm_entity', номер товара {cart_id}' "
            f"  в 'confirm_cart_handler' выполнен неуспешно: {e}"
        )
        return
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
    try:
        admins = get_all_admin(session)
        logger.info(
            f"'carts.confirm_cart_handler':  {call.from_user.id} получил данные 'get_all_admin' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'get_all_admin' "
            f"  в 'confirm_cart_handler' выполнен неуспешно: {e}"
        )
        return
    for admin in admins:
        await call.bot.send_message(chat_id=admin, text=f"{call.from_user.full_name} собрал заказ \n"
                                                        f" №: {cart.id}, всего {int (cart.total_items)} позиций")
    await call.answer()

# -------------------------------------------------------
#             Удаление корзины
# -------------------------------------------------------
@router.callback_query(F.data.startswith("Cart_delete:"))
async def delete_cart(call: CallbackQuery):
    """Delete Cart"""
    _, cart_id = call.data.split(":")
    try:
        cart_id = int(cart_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {cart_id} в целое "
            f"  в 'delete_cart' выполнен неуспешно: {e}"
        )
        return
    await call.message.edit_reply_markup(reply_markup=delete_confirm_kb(int(cart_id), "Cart"))
    await call.answer()


@router.callback_query(F.data.startswith("Cart_delete_confirm:"))
async def delete_cart_confirm(call: CallbackQuery):
    """Обработка подтверждения удаления корзины """
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'delete_cart_confirm' выполнен неуспешно: {e}"
        )
        return
    try:
        delete_entity(session, int(item_id), Cart)
        logger.info(
            f"'carts.delete_cart_confirm':  {call.from_user.id} получил данные 'delete_entity' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'delete_entity' "
            f"  в 'delete_cart_confirm' выполнен неуспешно: {e}"
        )
        return
    await call.message.edit_text("🗑 Заказ удалён")
    await call.answer()


@router.callback_query(F.data.startswith("Cart_delete_cancel:"))
async def delete_cancel(call: CallbackQuery):
    """Обработка отмены корзины и перерисовка сообщения"""
    _, item_id = call.data.split(":")
    try:
        item_id = int(item_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} преобразование номера товара {item_id} в целое "
            f"  в 'delete_cancel' выполнен неуспешно: {e}"
        )
        return
    try:
        item = get_entity_by_id(session, int(item_id), Cart)
        logger.info(
            f"'carts.delete_cancel':  {call.from_user.id} получил данные 'get_entity_by_id' "
        )
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {call.from_user.id} в БД 'get_entity_by_id' "
            f"  в 'delete_cancel' выполнен неуспешно: {e}"
        )
        return
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
    user_cart_messages.clear()
    await call.answer("Экран очищен")


# -------------------------------------------------------
#                Показ предыдущих корзин
# -------------------------------------------------------
@router.callback_query(F.data == "previous_cart")
async def show_previus_cart(callback: CallbackQuery):
    """Вывод предыдущих корзин пользователя"""
    user_cart_messages[callback.from_user.id] = []
    try:
        user_id = get_costumer_id(session, callback.from_user.id)
        previous_carts: Sequence[Any] = get_entity_by_user_id(session, user_id, Cart)
        logger.info(
            f"'carts.show_previus_cart':  {callback.from_user.id} получил данные 'get_costumer_id' и 'get_entity_by_user_id'"
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
                f"'carts.show_previus_cart':  {callback.from_user.id} получил данные 'get_all_categories'"
            )
        except Exception as e:
            logger.exception(
                f" Запрос пользователя {callback.from_user.id} в БД 'get_all_categories' "
                f"  в 'show_previus_cart' выполнен неуспешно: {e}"
            )
            return
        await callback.message.edit_text("У вас не было покупок до настоящего момента, \n"
                                      "выберите товары в нашем каталоге",
                                      reply_markup=get_categories_kb(categories))
        await callback.answer()
        return
    else:  # Вывод на экран предыдущих корзин
        await callback.message.edit_text(
            "Список Ваших заказов:",
            reply_markup=previous_cartlist_kb(previous_carts),
        )
        user_cart_messages[callback.from_user.id].append(callback.message.message_id)
        await callback.answer()


@router.callback_query(F.data.startswith("previous_cart_"))
async def show_previus_item(callback: CallbackQuery):
    """Вывод товаров из предыдущих корзин"""
    _, _, cart_id = callback.data.split("_")
    try:
        cart_id = int(cart_id)
    except Exception as e:
        logger.exception(
            f" Запрос пользователя {callback.from_user.id} преобразование номера товара {cart_id} в целое "
            f"  в 'delete_cancel' выполнен неуспешно: {e}"
        )
        return
    try:
        items = get_entity_items(session, cart_id, CartItems)
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
    if user_id not in user_cart_messages:
        user_cart_messages[user_id] = []
    user_cart_messages[user_id].append(start_msg.message_id)
    for item in items:
        msg = await callback.message.answer(text = f"✅ <b>{item.product.name}</b>\n"
                                            f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
                                            f"Стоимость: <b>{item.total_price:.2f} ₽</b>"
        )
        user_cart_messages[user_id].append(msg.message_id)
    back_msg = await callback.message.answer(text="Для возрата к списку заказов нажмите 👇",
                                             reply_markup=back_kb())
    user_cart_messages[callback.from_user.id].append(back_msg.message_id)
    if user_id in user_cart_messages and user_cart_messages[user_id]:
        # Удаляем и возвращаем первый элемент
        user_cart_messages[user_id].pop(0)
