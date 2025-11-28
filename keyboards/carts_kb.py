from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton as Btn


# Клавиатура управления товаром
def item_action_kb(item_id: int, model: str):
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
def delete_confirm_kb(item_id: int, model: str):
    kb = InlineKeyboardBuilder()
    kb.row(
        Btn(text="Удалить", callback_data=f"{model}_delete_confirm:{item_id}"),
        Btn(text="Отмена", callback_data=f"{model}_delete_cancel:{item_id}")
    )
    return kb.as_markup()


# Клавиатура корзины
def cart_main_kb(cart_id: int, model: str):
    kb = InlineKeyboardBuilder()
    kb.row(
        Btn(text="✅ Подтвердить заказ", callback_data=f"{model}_confirm:{cart_id}"),
        Btn(text="❌ Удалить заказ", callback_data=f"{model}_delete:{cart_id}")
    )
    kb.row(
        Btn(text="🔙 Выйти из корзины", callback_data=f"{model}_cleanup")
    )
    return kb.as_markup()
