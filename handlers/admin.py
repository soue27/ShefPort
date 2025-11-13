
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from data.config import SUPERADMIN_ID
from datadase.db import get_new_questions, session, get_question_by_id, save_answer, get_all_costumer_for_mailing, save_news
from keyboards.admin_kb import main_kb, check_questions, get_questions, mailing_kb, confirm_kb
from services.filters import IsAdmin


router = Router(name='admin')


class AnswerQuestion(StatesGroup):
    answer = State()


class TextMailing(StatesGroup):
    title = State()
    post = State()
    url = State()


class ImageMailing(StatesGroup):
    title = State()
    post = State()
    url = State()
    image_url = State()


class MailingStates(StatesGroup):
    waiting_content = State()
    waiting_confirmation = State()


@router.message(Command("admin"), IsAdmin())
async def admin_start(message: Message) -> None:
    """Обработка команды /admin"""
    await message.answer(f"Привет! Добро пожаловать Админ {message.from_user.full_name}", reply_markup=main_kb())


@router.callback_query(F.data == "check_questions")
async def show_questions(callback: CallbackQuery) -> None:
    """Обработка кнопки check_questions"""
    await callback.message.delete()
    await callback.message.answer("Сообщения:", reply_markup=check_questions())


@router.callback_query(F.data == "new_questions")
async def show_questions(callback: CallbackQuery) -> None:
    """Обработка кнопки просмотра новых сообщений"""
    questions = get_new_questions(session)
    await callback.message.answer("Сообщения:", reply_markup=get_questions(questions))


@router.callback_query(F.data.startswith("question_"))
async def get_answer(callback: CallbackQuery, state: FSMContext) -> None:
    questions_id = int(callback.data.split("_")[1])
    question = get_question_by_id(session, questions_id)
    #Сохранение данных в state, для передачи в следующую функцию
    await state.update_data(questions_id=question.id)
    await state.update_data(tg_id=question.user_id)
    await state.update_data(question_text=question.text)
    #Вывод сервисных сообщений админу
    await callback.message.delete()
    await callback.message.answer(f"Сообщение: {question.text}")
    await callback.message.answer(f"Введите ответ")
    await state.set_state(AnswerQuestion.answer)


@router.message(AnswerQuestion.answer)
async def handle_answer(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработка ответа админа на сообщение пользователя отправка

    :param message: Message - сообщение от пользователя
    :param state: FSMContext - контекст FSM
    :param bot: Bot - бот, который отправляет сообщения
    """
    #Получение данных из стейта
    data = await state.get_data()
    text_otveta = message.text
    questions_id = data.get('questions_id')
    tg_id = data.get('tg_id')
    #Подготовка текста ответа
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


#Обработка ввода и отправки рассылок
async def send_news(data: dict, users: list, bot: Bot):
    """Функция для рассылки новостей, также исполльзуется для предпросмотра
    :param data - словарь с данными
    :param users - списко рассылки, для предпросмотра используется один айди
    :param bot - экземплыр класса.
    """
    mypost = (f"<b>{data['title']}</b>\n"
              f"{data['post']})\n")
    if data["url"] not in ("нет", "Нет"):
        url_text = f'<a href="{data["url"]}">Подробнее...</a>'
    else:
        url_text = f'<a href="https://vk.com/fish_chus">Наша группа ВК</a>'
    if data['type'] == 'image':
        for user in users:
            await bot.send_photo(chat_id=user, photo=data['photo'], caption=mypost)
            await bot.send_message(chat_id=user, text=url_text ,  disable_web_page_preview=True)
    elif data['type'] == 'film':
        for user in users:
            await bot.send_video(chat_id=user, video=data['photo'], caption=mypost)
            await bot.send_message(chat_id=user, text=url_text, disable_web_page_preview=True)
    else:
        for user in users:
            await bot.send_message(chat_id=user, text=f"{mypost} {url_text}" ,  disable_web_page_preview=True)
    save_news(session, data)



@router.callback_query(F.data == "mailing")
async def show_mailing_types(callback: CallbackQuery) -> None:
    """Обработка нажатия ккнопки Расслыка в меню"""
    await callback.message.answer("Выберите формат поста", reply_markup=mailing_kb())


@router.callback_query(F.data.startswith("post_"))
async def show_mailing(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка ввода текста заголовка"""
    await callback.message.answer("Введите заголовок сообщения:")
    if callback.data.split("_")[1] == 'text':
        await state.set_state(TextMailing.title)
    else:
        await state.set_state(ImageMailing.title)


@router.message(TextMailing.title)
async def handle_texttitle(message: Message, state: FSMContext):
    """Обработка ввода текста поста"""
    await state.update_data(title=message.text)
    await message.answer("Введите текст поста:")
    await state.set_state(TextMailing.post)


@router.message(TextMailing.post)
async def handle_textpost(message: Message, state: FSMContext):
    """Обработка ввода внешней ссылки"""
    await state.update_data(post=message.text)
    await message.answer("Добавьте ссылку на пост")
    await state.set_state(TextMailing.url)


@router.message(TextMailing.url)
async def handle_texturl(message: Message, state: FSMContext, bot: Bot):
    """Обработка поста, отправка и сохранение поста"""
    await state.update_data(url=message.text)
    await state.update_data(type='text')
    # mypost = (f"<b>{my_data['title']}</b>\n"
    #           f"{my_data['post']})\n")
    # if my_data["url"] not in ("нет", "Нет"):
    #     mypost += f'<a href="{my_data["url"]}">Подробнее...</a>'
    # await message.answer(mypost, reply_markup=confirm_kb(), disable_web_page_preview=True)
    my_data = await state.get_data()
    user = [message.from_user.id]
    await send_news(my_data, user, bot)
    await state.set_state(MailingStates.waiting_confirmation)
    await state.update_data(mailing_content=my_data)
    await message.answer("Подтвердите для рассылки", reply_markup=confirm_kb())


@router.message(ImageMailing.title)
async def handle_imagetitle(message: Message, state: FSMContext):
    """Обработка ввода текста поста"""
    await state.update_data(title=message.text)
    await message.answer("Введите текст поста:")
    await state.set_state(ImageMailing.post)


@router.message(ImageMailing.post)
async def handle_imagepost(message: Message, state: FSMContext):
    """Обработка ввода внешней ссылки"""
    await state.update_data(post=message.text)
    await message.answer("Добавьте ссылку на пост")
    await state.set_state(ImageMailing.url)


@router.message(ImageMailing.url)
async def handle_imageurl(message: Message, state: FSMContext):
    """Обработка ввода изображения"""
    await state.update_data(url=message.text)
    await message.answer("Добавьте фото/видео")
    await state.set_state(ImageMailing.image_url)


@router.message(ImageMailing.image_url, F.photo | F.video)
async def handle_texttimageurl(message: Message, state: FSMContext, bot: Bot):
    """Обработка поста, отправка и сохранение поста"""
    if message.photo:
        await state.update_data(photo=message.photo[-1].file_id, type="image")
    else:
        await state.update_data(photo=message.video.file_id, type="film")
    my_data = await state.get_data()
    user = [message.from_user.id]
    await send_news(my_data, user, bot)
    await state.set_state(MailingStates.waiting_confirmation)
    await state.update_data(mailing_content=my_data)
    await message.answer("Подтвердите для рассылки",reply_markup=confirm_kb())


@router.callback_query(F.data.startswith("mailing_"), MailingStates.waiting_confirmation)
async def show_mailing_types(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Обработка нажатия кнопки Рассылка в меню"""
    # Получаем сохраненные данные
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
    Send file to admin.

    Args:
        file_path (str): Path to file.
        bot (Bot): Bot instance.

    """
    user_id = SUPERADMIN_ID
    file_path = file_path
    document = FSInputFile(file_path)
    await bot.send_document(chat_id=user_id, document=document, caption="Необходимо добавить в БД данные позиции")

