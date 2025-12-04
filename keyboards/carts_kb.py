from typing import Sequence, Any

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup


# Клавиатура управления товаром
def item_action_kb(item_id: int, model: str) -> InlineKeyboardMarkup:
    """
    Клавиатура управления товаром. Передаем cart или order по надобности
    """
    kb = InlineKeyboardBuilder()
    kb.row(
        Btn(text="➕", callback_data=f"{model}_plus:{item_id}"),
        Btn(text="➖", callback_data=f"{model}_minus:{item_id}"),
        Btn(text="❌ Удалить", callback_data=f"{model}_delete:{item_id}")
    )

    return kb.as_markup()


# Подтверждение удаления
def delete_confirm_kb(item_id: int, model: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        Btn(text="Удалить", callback_data=f"{model}_delete_confirm:{item_id}"),
        Btn(text="Отмена", callback_data=f"{model}_delete_cancel:{item_id}")
    )
    return kb.as_markup()


# Клавиатура корзины
def cart_main_kb(cart_id: int, model: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        Btn(text="✅ Подтвердить заказ", callback_data=f"{model}_confirm:{cart_id}"),
        Btn(text="❌ Удалить заказ", callback_data=f"{model}_delete:{cart_id}")
    )
    kb.row(
        Btn(text="🔙 Выйти из корзины", callback_data=f"{model}_cleanup")
    )
    return kb.as_markup()


def previous_cart_kb() -> InlineKeyboardMarkup:
    """Клавиатура для перехода к просмотру предыдущих заказов"""
    kb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    kb.button(text="Просмотр предыдущих заказов", callback_data="previous_cart")
    return kb.as_markup()


def previous_cartlist_kb(cart_list: Sequence[Any]) -> InlineKeyboardMarkup:
    """Клавиатура для показа списка корзин пользователя"""
    kb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    for cart in cart_list:
        kb.button(text=f"🛒 Заказ №{cart.id} от {cart.created_at.strftime('%d.%m.%Y')} г.",
                  callback_data=f"previous_cart_{cart.id}")

    kb.button(text="🔙 Назад", callback_data="Cart_cleanup")
    kb.adjust(1)
    return kb.as_markup()


def back_kb() -> InlineKeyboardMarkup:
    """Клавиатура для возрата"""
    kb: InlineKeyboardBuilder = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="Cart_cleanup")
    kb.adjust(1)
    return kb.as_markup()

# </b> <b>