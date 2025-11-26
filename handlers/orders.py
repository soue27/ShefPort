from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from data.config import SUPERADMIN_ID
from database.db import get_new_questions, session, get_question_by_id, save_answer, get_all_costumer_for_mailing, save_news
from keyboards.admin_kb import main_kb, check_questions, get_questions, mailing_kb, confirm_kb
from services.filters import IsAdmin


router = Router(name='orders')