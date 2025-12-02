"""
Модуль обработчиков административных команд и функций бота.

Этот модуль содержит обработчики для административной части бота, включая:
- Управление вопросами и ответами пользователей
- Рассылку сообщений (текстовые и с изображениями)
- Управление заказами и корзинами
- Загрузку данных из файлов

Основные компоненты:
- Роутер: router - основной роутер для административных команд
- Состояния: Классы состояний для FSM (AnswerQuestion, TextMailing, ImageMailing, MailingStates, CommentStates)
- Обработчики: Функции, обрабатывающие команды и сообщения администратора

Основные параметры, используемые в обработчиках:
- callback: CallbackQuery - объект callback-запроса от кнопок
- message: Message - объект сообщения от пользователя
- state: FSMContext - контекст конечного автомата состояний
- bot: Bot - экземпляр бота для отправки сообщений
- callback.data: str - данные callback-запроса, содержащие команду и параметры

Пример использования:
    Для добавления нового обработчика используйте декоратор @router с указанием типа обновления,
    например: @router.message(Command("команда")) или @router.callback_query(F.data == "действие")
"""

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from data.config import SUPERADMIN_ID
from database.db import (
    get_new_questions,
    session,
    get_question_by_id,
    save_answer,
    get_all_costumer_for_mailing,
    save_news,
    load_data,
    engine,
    get_entity_for_done,
    get_entity_items,
    get_entity_by_id,
    get_costumer_tgid,
    set_entity_for_issue,
    get_entity_for_issued,
    set_entity_close,
)
from database.models import Cart, CartItems
from keyboards.admin_kb import (
    main_kb,
    check_questions,
    get_questions,
    mailing_kb,
    confirm_kb,
    get_entity_kb,
    get_admin_confirmentity_kb,
    get_close_entity,
    get_issued_entity,
)
from services.filters import IsAdmin


router = Router(name='admin')

user_cart_messages = {}


class AnswerQuestion(StatesGroup):
    """
    Состояния для обработки ответов на вопросы пользователей.
    """
    answer = State()


class TextMailing(StatesGroup):
    """
    Состояния для текстовой рассылки.
    
    Атрибуты:
        title: Состояние для ввода заголовка рассылки
        post: Состояние для ввода текста рассылки
        url: Состояние для ввода ссылки в рассылке
    """
    title = State()
    post = State()
    url = State()


class ImageMailing(StatesGroup):
    """
    Состояния для рассылки с изображением.
    
    Атрибуты:
        title: Состояние для ввода заголовка
        post: Состояние для ввода текста
        url: Состояние для ввода ссылки
        image_url: Состояние для загрузки изображения
    """
    title = State()
    post = State()
    url = State()
    image_url = State()


class MailingStates(StatesGroup):
    """
    Состояния для процесса рассылки.
    
    Атрибуты:
        waiting_content: Ожидание контента для рассылки
        waiting_confirmation: Ожидание подтверждения рассылки
    """
    waiting_content = State()
    waiting_confirmation = State()


class CommentStates(StatesGroup):
    Comment = State()


@router.message(Command("admin"), IsAdmin())
async def admin_start(message: Message) -> None:
    """
    Обработчик команды /admin.
    
    Приветствует администратора и отображает главное меню.
    
    Args:
        message: Объект сообщения от пользователя
    """
    await message.answer(f"Привет! Добро пожаловать Админ {message.from_user.full_name}", reply_markup=main_kb())


@router.callback_query(F.data == "check_questions")
async def show_questions(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки проверки вопросов.
    
    Удаляет предыдущее сообщение и отображает список сообщений.
    
    Args:
        callback: Объект callback-запроса
    """
    await callback.message.delete()
    await callback.message.answer("Сообщения:", reply_markup=check_questions())


@router.callback_query(F.data == "new_questions")
async def show_new_questions(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки просмотра новых сообщений.
    
    Получает новые вопросы из базы данных и отображает их.
    
    Args:
        callback: Объект callback-запроса
    """
    questions = get_new_questions(session)
    await callback.message.answer("Сообщения:", reply_markup=get_questions(questions))


@router.callback_query(F.data.startswith("question_"))
async def get_answer(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора вопроса для ответа.
    
    Извлекает ID вопроса из callback-данных, загружает вопрос из базы данных
    и переводит бота в состояние ожидания ответа.
    
    Args:
        callback: Объект callback-запроса
        state: Контекст состояния FSM
    """
    questions_id = int(callback.data.split("_")[1])
    question = get_question_by_id(session, questions_id)
    # Сохранение данных в state, для передачи в следующую функцию
    await state.update_data(questions_id=question.id)
    await state.update_data(tg_id=question.user_id)
    await state.update_data(question_text=question.text)
    # Вывод сервисных сообщений админу
    await callback.message.delete()
    await callback.message.answer(f"Сообщение: {question.text}")
    await callback.message.answer("Введите ответ")
    await state.set_state(AnswerQuestion.answer)


@router.message(AnswerQuestion.answer)
async def handle_answer(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработка ответа админа на сообщение пользователя отправка
    
    Args:
        message: Message - сообщение от пользователя
        state: FSMContext - контекст FSM
        bot: Bot - бот, который отправляет сообщения
    """
    # Получение данных из стейта
    data = await state.get_data()
    text_otveta = message.text
    questions_id = data.get('questions_id')
    tg_id = data.get('tg_id')
    # Подготовка текста ответа
    vopros = data.get('question_text')
    start = f"Ответ от администрации на Ваш вопрос: {vopros}:"
    # Отправка ответа и сохранение ответа в БД
    await bot.send_message(chat_id=tg_id, text=start)
    await bot.send_message(chat_id=tg_id, text=f'{text_otveta}')
    if save_answer(session, questions_id, text_otveta):
        await message.answer("Ответ отправлен")
    else:
        await message.answer("Ошибка при отправке ответа")
    await state.clear()


# Обработка ввода и отправки рассылок
async def send_news(data: dict, users: list, bot: Bot):
    """
    Функция для рассылки новостей, также исполльзуется для предпросмотра.
    
    Args:
        data: Словарь с данными для рассылки
        users: Список пользователей для рассылки
        bot: Экземпляр бота для отправки сообщений
    """
    mypost = (f"<b>{data['title']}</b>\n"
              f"{data['post']})\n")
    if data["url"] not in ("нет", "Нет"):
        url_text = f'<a href="{data["url"]}">Подробнее...</a>'
    else:
        url_text = '<a href="https://vk.com/fish_chus">Наша группа ВК</a>'
    if data['type'] == 'image':
        for user in users:
            await bot.send_photo(chat_id=user, photo=data['photo'], caption=mypost)
            await bot.send_message(chat_id=user, text=url_text, disable_web_page_preview=True)
    elif data['type'] == 'film':
        for user in users:
            await bot.send_video(chat_id=user, video=data['photo'], caption=mypost)
            await bot.send_message(chat_id=user, text=url_text, disable_web_page_preview=True)
    else:
        for user in users:
            await bot.send_message(chat_id=user, text=f"{mypost} {url_text}", disable_web_page_preview=True)
    # save_news(session, data)


@router.callback_query(F.data == "mailing")
async def show_mailing_types(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки "Рассылка" в меню.
    
    Отображает доступные форматы постов для рассылки.
    
    Args:
        callback: Объект callback-запроса
    """
    await callback.message.answer("Выберите формат поста", reply_markup=mailing_kb())


@router.callback_query(F.data.startswith("post_"))
async def show_mailing(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора типа поста для рассылки.
    
    В зависимости от выбранного типа поста (текст/изображение) переводит
    бота в соответствующее состояние для ввода заголовка.
    
    Args:
        callback: Объект callback-запроса
        state: Контекст состояния FSM
    """
    await callback.message.answer("Введите заголовок сообщения:")
    if callback.data.split("_")[1] == 'text':
        await state.set_state(TextMailing.title)
    else:
        await state.set_state(ImageMailing.title)


@router.message(TextMailing.title)
async def handle_texttitle(message: Message, state: FSMContext):
    """
    Обработчик ввода заголовка текстовой рассылки.
    
    Сохраняет заголовок в состояние и запрашивает текст поста.
    
    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
    """
    await state.update_data(title=message.text)
    await message.answer("Введите текст поста:")
    await state.set_state(TextMailing.post)


@router.message(TextMailing.post)
async def handle_textpost(message: Message, state: FSMContext):
    """
    Обработчик ввода текста поста для рассылки.
    
    Сохраняет текст поста в состояние и запрашивает ссылку.
    
    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
    """
    await state.update_data(post=message.text)
    await message.answer("Добавьте ссылку на пост")
    await state.set_state(TextMailing.url)


@router.message(TextMailing.url)
async def handle_texturl(message: Message, state: FSMContext, bot: Bot):
    """
    Обработчик ввода ссылки для текстовой рассылки.
    
    Сохраняет ссылку, отправляет предпросмотр и запрашивает подтверждение.
    
    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
        bot: Экземпляр бота для отправки сообщений
    """
    await state.update_data(url=message.text)
    await state.update_data(type='text')
    my_data = await state.get_data()
    user = [message.from_user.id]
    await send_news(my_data, user, bot)
    await state.set_state(MailingStates.waiting_confirmation)
    await state.update_data(mailing_content=my_data)
    await message.answer("Подтвердите для рассылки", reply_markup=confirm_kb())


@router.message(ImageMailing.title)
async def handle_imagetitle(message: Message, state: FSMContext):
    """
    Обработчик ввода заголовка для рассылки с изображением.
    
    Сохраняет заголовок и запрашивает текст поста.
    
    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
    """
    await state.update_data(title=message.text)
    await message.answer("Введите текст поста:")
    await state.set_state(ImageMailing.post)


@router.message(ImageMailing.post)
async def handle_imagepost(message: Message, state: FSMContext):
    """
    Обработчик ввода текста поста для рассылки с изображением.
    
    Сохраняет текст поста и запрашивает ссылку.
    
    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
    """
    await state.update_data(post=message.text)
    await message.answer("Добавьте ссылку на пост")
    await state.set_state(ImageMailing.url)


@router.message(ImageMailing.url)
async def handle_imageurl(message: Message, state: FSMContext):
    """
    Обработчик ввода ссылки для рассылки с изображением.
    
    Сохраняет ссылку и запрашивает изображение или видео.
    
    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
    """
    await state.update_data(url=message.text)
    await message.answer("Добавьте фото/видео")
    await state.set_state(ImageMailing.image_url)


@router.message(ImageMailing.image_url, F.photo | F.video)
async def handle_texttimageurl(message: Message, state: FSMContext, bot: Bot):
    """
    Обработчик загрузки изображения или видео для рассылки.
    
    Сохраняет изображение или видео, отправляет предпросмотр и запрашивает подтверждение.
    
    Args:
        message: Объект сообщения от пользователя
        state: Контекст состояния FSM
        bot: Экземпляр бота для отправки сообщений
    """
    if message.photo:
        await state.update_data(photo=message.photo[-1].file_id, type="image")
    else:
        await state.update_data(photo=message.video.file_id, type="film")
    my_data = await state.get_data()
    user = [message.from_user.id]
    await send_news(my_data, user, bot)
    await state.set_state(MailingStates.waiting_confirmation)
    await state.update_data(mailing_content=my_data)
    await message.answer("Подтвердите для рассылки", reply_markup=confirm_kb())


@router.callback_query(F.data.startswith("mailing_"), MailingStates.waiting_confirmation)
async def show_mailing_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик подтверждения или отмены рассылки.
    
    В зависимости от выбора пользователя либо отменяет рассылку,
    либо отправляет её всем пользователям.
    
    Args:
        callback: Объект callback-запроса
        state: Контекст состояния FSM
        bot: Экземпляр бота для отправки сообщений
    """
    if callback.data.split("_")[1] == 'cancel':
        await callback.message.answer("Выберите тип сообщения:", reply_markup=mailing_kb())
    elif callback.data.split("_")[1] == 'confirm':
        data = await state.get_data()
        my_data = data.get('mailing_content')
        users = get_all_costumer_for_mailing(session)
        if my_data:
            await send_news(data=my_data, users=users, bot=bot)
            save_news(session, my_data)
        await callback.message.answer("Сообщение отправлено")
        await state.clear()


async def send_file_to_admin(file_path: str, bot: Bot):
    """
    Send file to superadmin.
    
    Args:
        file_path (str): Path to file.
        bot (Bot): Bot instance.
    """
    user_id = SUPERADMIN_ID
    file_path = file_path
    document = FSInputFile(file_path)
    await bot.send_document(chat_id=user_id, document=document, caption="Необходимо добавить в БД данные позиции")


@router.message(F.document, IsAdmin())
async def load_dates(message: Message, bot: Bot):
    """
    Обработчик загрузки файла с данными.
    
    Загружает Excel-файл, сохраняет его и загружает данные в базу.
    
    Args:
        message: Объект сообщения с прикрепленным файлом
        bot: Экземпляр бота для работы с файлами
    """
    file_idx = message.document.file_id
    file = await bot.get_file(file_id=file_idx)
    file_path = file.file_path
    print(file, file_path)
    await bot.download_file(file_path, "data/forload.xlsx")
    count = load_data("data/forload.xlsx", engine=engine)
    if count != 0:
        await message.answer(f"Загружено {count} позиций")
    else:
        await message.answer("Ошибка загрузки позиций")


#*******************************
# Работа с корзиной для админа
#******************************
@router.callback_query(F.data == "done_carts")
async def show_done_carts(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки просмотра заказов для сбора.
    
    Получает список заказов, готовых к выдаче, и отображает их.
    
    Args:
        callback: Объект callback-запроса
    """
    entities = get_entity_for_done(session, Cart)
    await callback.message.answer("Заказы для сбора:", reply_markup=get_entity_kb(entities, Cart))


@router.callback_query(F.data.startswith("Cart_"))
async def show_cart_for_done(callback: CallbackQuery):
    """
    Обработчик просмотра содержимого корзины.
    
    Отображает все товары в заказе с деталями и кнопками управления.
    
    Args:
        callback: Объект callback-запроса с ID корзины
    """
    cart_id = int(callback.data.split("_")[1])
    items = get_entity_items(session, cart_id, CartItems)
    user_id = callback.from_user.id
    user_cart_messages[user_id] = []
    # Вывод всех товаров как отдельные сообщения
    for item in items:
        text = (
            f"🛒 <b>{item.product.name}</b>\n"
            f"Количество: <b>{item.quantity}</b> {item.product.unit}\n"
            f"Стоимость: <b>{item.total_price:.2f} ₽</b>"
        )
        sent_message = await callback.message.answer(text=text, parse_mode=ParseMode.HTML)
        user_cart_messages[user_id].append(sent_message.message_id)
    
    # Отправка кнопок управления заказом в зависимости от подготовки или выдачи заказа
    if not get_entity_by_id(session, cart_id, Cart).is_issued:
        buttons_message = await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_admin_confirmentity_kb(cart_id, "Cart"),
            parse_mode="Markdown"
        )
        user_cart_messages[user_id].append(buttons_message.message_id)
    else:
        buttons_message = await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_issued_entity(cart_id, "Cart"),
            parse_mode="Markdown",
        )
        user_cart_messages[user_id].append(buttons_message.message_id)


@router.callback_query(F.data.startswith("Back"))
async def go_back(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки возврата в меню.
    
    Удаляет все сообщения, связанные с текущей корзиной, и очищает историю сообщений.
    
    Args:
        callback: Объект callback-запроса с данными кнопки
        
    Returns:
        None
    """
    user_id = callback.from_user.id

    if user_id in user_cart_messages:
        for mid in user_cart_messages[user_id]:
            await callback.bot.delete_message(user_id, mid)
        del user_cart_messages[user_id]

    await callback.answer("Экран очищен")


@router.callback_query(F.data.startswith("CartDone_"))
async def get_cart_for_done(callback: CallbackQuery) -> None:
    """
    Обработчик подтверждения завершения сбора корзины.
    
    Отображает меню действий с корзиной после подтверждения её сбора.
    
    Args:
        callback: Объект callback-запроса с ID корзины в формате "CartDone_<id>"
        
    Returns:
        None
    """
    user_id = callback.from_user.id
    cart_id = int(callback.data.split("_")[1])
    sent_message = await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_close_entity(cart_id, "Cart"),
        parse_mode=ParseMode.HTML
    )
    user_cart_messages[user_id].append(sent_message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("CartDoneMessage_"))
async def mess_cart_for_done(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик уведомления клиента о готовности заказа.
    
    В зависимости от выбранного действия либо сразу уведомляет клиента о готовности заказа,
    либо запрашивает дополнительный комментарий для уведомления.
    
    Args:
        callback: Объект callback-запроса с ID корзины в формате "CartDoneMessage_<id>" или "CartDoneMessage_comm_<id>"
        state: Контекст состояния FSM для хранения данных между шагами
        bot: Экземпляр бота для отправки сообщений
        
    Returns:
        None
    """
    cart_id = int(callback.data.split("_")[1]) if callback.data.split("_")[1] != "comm" else int(callback.data.split("_")[2])
    entity = get_entity_by_id(session, cart_id, Cart)
    user = await bot.get_chat(get_costumer_tgid(session, entity.user_id))
    name = "Клиент" if not user.full_name else user.full_name
    text = (f"Уважаемый {name}, Ваш заказ №{cart_id} готов к выдаче.\n"
            f"Ждем Вас в нашем магазине.")
    if callback.data.split("_")[1] != "comm":
        await bot.send_message(chat_id=user.id, text=text)
        await callback.message.answer(("Клиент уведомлен о готовности заказа \n"
                                       "заказ перешел в категорию 'Для выдачи'"))
        await callback.answer()
        set_entity_for_issue(session, cart_id, Cart)
        return
    else:
        await state.update_data(text=text)
        await state.update_data(user=user)
        await state.update_data(cart_id=cart_id)
        await callback.message.answer("Введите текст комментария")
        await state.set_state(CommentStates.Comment)
    await callback.answer()


@router.message(CommentStates.Comment)
async def handle_comment(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик ввода комментария для уведомления клиента.
    
    Получает комментарий от администратора, добавляет его к уведомлению и отправляет клиенту.
    
    Args:
        message: Объект сообщения с комментарием от администратора
        state: Контекст состояния FSM с данными о заказе и клиенте
        bot: Экземпляр бота для отправки сообщений
        
    Returns:
        None
    """
    await state.update_data(comment=message.text)
    my_data: dict = await state.get_data()
    user = my_data.get('user')
    cart_id: int = my_data.get('cart_id')
    text = f"{my_data.get('text')} \n {my_data.get('comment')}"
    await bot.send_message(chat_id=user.id, text=text)
    await message.answer(("Клиент уведомлен о готовности заказа. \n"
                          "Заказ перешел в категорию 'Для выдачи'"))
    set_entity_for_issue(session, cart_id, Cart)


@router.callback_query(F.data == "issued_carts")
async def show_issued_carts(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки просмотра заказов для выдачи клиенту.

    Получает список заказов, готовых к выдаче, и отображает их.

    Args:
        callback: Объект callback-запроса
    """
    entities = get_entity_for_issued(session, Cart)
    await callback.message.answer(
        "Заказы для выдачи:", reply_markup=get_entity_kb(entities, Cart)
    )


@router.callback_query(F.data.startswith("CartClose_"))
async def close_cart(callback: CallbackQuery) -> None:
    cart_id = int(callback.data.split("_")[1])
    set_entity_close(session, cart_id, Cart)
    await callback.message.answer("Заказ выдан клиенту. Работа с данным заказом закончена")
