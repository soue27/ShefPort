from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from data.config import SUPERADMIN_ID
from datadase.db import get_new_questions, session, get_question_by_id, save_answer
from keyboards.admin_kb import main_kb, check_questions, get_questions
from services.filters import IsAdmin


router = Router(name='admin')


class AnswerQuestion(StatesGroup):
    answer = State()


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
    print(questions)
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
async def handle_answer(message: Message, state: FSMContext, bot: Bot, ) -> None:
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

