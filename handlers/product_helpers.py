import asyncio
from datadase.db import get_products_by_category
from keyboards.product_cards import create_product_card_keyboard
from keyboards.catalog_control import create_control_keyboard


async def send_product_card(message, product, index=None, total=None):
    """
    Отправляет карточку товара в чат
    Args:
        message: Объект сообщения для ответа
        product: Объект товара
        index: Порядковый номер товара (для прогресса)
        total: Общее количество товаров (для прогресса)
    """
    try:
        # Подготовка данных
        progress_text = f"({index}/{total})" if index and total else ""
        description_preview = product.description[:100] + "..." if len(
            product.description) > 100 else product.description
        description_preview = description_preview.removeprefix("Описание")

        # Оптимизация изображения
        optimized_image = product.image
        print(optimized_image)
        keyboard = create_product_card_keyboard(product.id)

        # Отправка карточки
        if optimized_image:
            await message.answer_photo(
                photo=optimized_image,
                caption=f"<b>{product.name}</b> {progress_text}\n\n"
                        f"📝 {description_preview}\n"
                        f"💵 <b>Цена: {product.price} руб</b>\n"
                        f"📦 <b>В наличии: 5000 шт</b>",
                parse_mode="HTML",
                reply_markup=keyboard.as_markup(),
                disable_notification=True
            )
        else:
            # Резервный вариант без изображения
            await message.answer(
                f"<b>{product.name}</b> {progress_text}\n\n"
                f"📝 {description_preview}\n"
                f"💵 <b>Цена: {product.price} руб</b>\n"
                f"📦 <b>В наличии: 4000 шт</b>",
                parse_mode="HTML",
                reply_markup=keyboard.as_markup(),
                disable_notification=True
            )

    except Exception as e:
        print(f"Ошибка отправки карточки товара {product.id}: {e}")
        # Аварийный вариант
        keyboard = create_product_card_keyboard(product.id)
        await message.answer(
            f"<b>{product.name}</b>\n"
            f"💵 <b>Цена: {product.price} руб</b>\n"
            f"📦 <b>В наличии: 3000 шт</b>",
            parse_mode="HTML",
            reply_markup=keyboard.as_markup(),
            disable_notification=True
        )


async def send_products_batch(message, products, category_id, offset=0, batch_size=5):
    """
    Отправляет порцию товаров с контролем продолжения
    Args:
        message: Объект сообщения для ответа
        products: Полный список товаров категории
        category_id: ID текущей категории
        offset: Смещение для текущей порции
        batch_size: Размер порции товаров
    """
    # Текущая порция товаров
    current_batch = products[offset:offset + batch_size]
    total_products = len(products)

    # Отправка товаров текущей порции
    for i, product in enumerate(current_batch):
        current_index = offset + i + 1
        await send_product_card(message, product, current_index, total_products)

        # Небольшая пауза между карточками для лучшего UX
        if i < len(current_batch) - 1:
            await asyncio.sleep(0.3)

    # Отправка контроллера навигации
    await send_control_message(message, category_id, offset, total_products, batch_size)


async def send_control_message(message, category_id, current_offset, total_products, batch_size=5):
    """
    Отправляет сообщение с управлением просмотром
    """
    control_keyboard = create_control_keyboard(
        category_id, current_offset, total_products, batch_size
    )

    progress_text = (
        f"📊 <b>Прогресс просмотра:</b> {current_offset + batch_size}/{total_products} товаров\n\n"
        "Выберите действие:"
    )

    await message.answer(
        progress_text,
        parse_mode="HTML",
        reply_markup=control_keyboard.as_markup(),
        disable_notification=True
    )


async def start_category_products(message, category_id, session):
    """
    Начинает показ товаров выбранной категории
    Args:
        message: Объект сообщения
        category_id: ID выбранной категории
        session: Сессия базы данных
    """
    # Получаем товары категории
    products = get_products_by_category(session, category_id)

    if not products:
        await message.answer("😔 В этой категории пока нет товаров")
        return

    # Информация о начале просмотра
    await message.answer(
        f"📦 <b>Найдено {len(products)} товаров в категории</b>\n"
        "Начинаем показ...",
        parse_mode="HTML",
        disable_notification=True
    )

    # Запускаем показ первой порции
    await send_products_batch(message, products, category_id, offset=0)