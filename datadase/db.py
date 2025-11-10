"""
Module datadase.db

This module contains functions for working with database.

It creates a database engine, creates all tables in database and provides a session object for querying database.

It also provides a function for saving user data to database.

"""
import re
from datetime import datetime
from typing import Type, Optional, List, Any
from zoneinfo import ZoneInfo

from sqlalchemy import select, func
from aiogram.types import CallbackQuery
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase

from data.config import DB_URL, ECHO
from datadase.models import Base, Costumer, Product, Category, Question
from services.search import normalize_text


engine = create_engine(DB_URL, echo=ECHO)
Base.metadata.create_all(engine)
session = Session(engine)
connect = engine.connect()

TOKEN_RE = re.compile(r"[а-яё]+", re.IGNORECASE)


def save_costumer(session: Session, callback: CallbackQuery, news: bool):
    """
    Saves costumer data to database.

    If user is not found, creates a new Costumer object and saves it to database.
    If user is found, updates user's news field and saves it to database.

    :param session: Current database session
    :param callback: CallbackQuery object
    :param news: Boolean value indicating whether user wants to receive news or not
    :return: None
    """
    user_data = callback.from_user
    user_id = user_data.id
    costumer = session.query(Costumer).filter(Costumer.tg_id == user_id).first()
    if not costumer:
        with session as ses:
            costumer=Costumer(
                tg_id=user_id,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                news = news
            )
            ses.add(costumer)
            ses.commit()
    else:
        with session as ses:
            costumer.news = news
            costumer.updated_at = datetime.now()
            ses.commit()


def get_random_photo(session: Session):
    """
    Returns a random photo from the database. Для старта диалога с ботом.
    """
    stmt = select(Product).order_by(func.random()).limit(1)
    result = session.scalar(stmt)
    return result.main_image, result.name


def get_all_categories(session: Session):
    """
    Fetches all categories from the database.

    :param session: SQLAlchemy session for database operations
    :type session: Session
    :return: List of tuples containing category names and their IDs
    :rtype: list[tuple[str, int]]
    """
    stmt = select(Category.name, Category.id).order_by(Category.id)
    result = session.execute(stmt).all()
    session.close()
    return result


def get_products_by_category(session: Session, category_id: int):
    """
    Fetches all products belonging to a specific category.

    :param session: SQLAlchemy session for database operations
    :type session: Session
    :param category_id: ID of the category to filter products by
    :type category_id: int
    :return: List of Product objects matching the category
    :rtype: list[Product]
    """
    stmt = select(Product).where(Product.category_id == category_id)
    result = session.scalars(stmt).all()
    session.close()
    return result


def tokenize(text: str):
    return TOKEN_RE.findall(text)


def search_products(session: Session, query: str) -> list:
    """
    Performs a search in the Product.name field (without modifying the database),
    case-insensitive and accounting for all word forms.

    :param session: SQLAlchemy session for database operations
    :type session: Session
    :param query: Search query string
    :type query: str
    :return: List of Product objects matching the search query
    :rtype: list[Product]
    """
    query_forms = normalize_text(query)
    results = []
    for product in session.query(Product).all():
        name_forms = normalize_text(product.name)
        if query_forms & name_forms:  # есть пересечение
            results.append(product)
    return results


def get_product_description(session: Session, product_id: int) -> Product:
    """
    Fetches the description of a specific product.

    :param session: SQLAlchemy session for database operations
    :param product_id: ID of the product to fetch description for
    :return: Description of the product
    """
    product = session.query(Product.name, Product.image,Product.description,
                            Product.characteristics).filter(Product.id == product_id).first()
    return product


def is_admin(session: Session, user_id: int):
    """
    Checks if a user is an admin.

    :param session: SQLAlchemy session for database operations
    :param user_id: ID of the user to check
    :return: Boolean value indicating whether the user is an admin or not
    """
    stmt = select(Costumer.is_admin).where(Costumer.tg_id == user_id)
    result = session.scalar(stmt)
    return result


def get_costumer_id(session: Session, user_id: int):
    """
    Fetches the ID of a specific costumer.

    :param session: SQLAlchemy session for database operations
    :param user_id: ID of the costumer to fetch ID for
    :return: ID of the costumer
    """
    stmt = select(Costumer.id).where(Costumer.tg_id == user_id)
    result = session.scalar(stmt)
    return result


def save_question(session: Session, user_id: int, mess_id: int, text: str):
    """
    Saves a question to the database.

    :param session: SQLAlchemy session for database operations
    :param user_id: ТГ ID of the user who asked the question
    :param mess_id: ID of the question in Telegram
    :param text: Text of the question
    :return: None
    """
    with session as ses:
        question = Question(user_id=user_id, questions_id=mess_id, text=text)
        ses.add(question)
        ses.commit()


def get_all_questions(session: Session):
    """
    Fetches all questions from the database.

    :param session: SQLAlchemy session for database operations
    :return: List of Question objects
    """
    stmt = select(Question).order_by(Question.id)
    result = session.scalars(stmt).all()
    return result


def get_new_questions(session: Session):
    """
    Fetches all new questions from the database.

    :param session: SQLAlchemy session for database operations
    :return: List of Question objects
    """
    stmt = select(Question).where(Question.is_answered == False).order_by(Question.id)
    result = session.scalars(stmt).all()
    return result


def get_question_by_id(session: Session, question_id: int):
    """
    Fetches a specific question from the database.

    :param session: SQLAlchemy session for database operations
    :param question_id: ID of the question to fetch
    :return: Question object
    """
    stmt = select(Question).where(Question.id == question_id)
    result = session.scalar(stmt)
    return result


def count_model_records(session, model: Type[DeclarativeBase], filters: Optional[List[Any]] = None) -> int:
    """
    Универсальная функция для подсчета количества записей в таблице модели с поддержкой фильтров

    Args:
        session: SQLAlchemy session
        model: Класс модели SQLAlchemy
        filters: Список условий фильтрации (например, [User.is_active == False])

    Returns:
        int: Количество записей в таблице, соответствующих фильтрам
    filters=[User.is_active == False]
    filters=[Post.is_published == False]
    filters=[
            User.is_active == False,
            User.created_at < thirty_days_ago
        ]
    """
    stmt = select(func.count()).select_from(model)

        # Применяем фильтры если они переданы
    if filters:
        for filter_condition in filters:
            stmt = stmt.where(filter_condition)

    count = session.execute(stmt).scalar()
    return count or 0


def get_all_admin(session: Session):
    stmt = select(Costumer.tg_id).where(Costumer.is_admin == True)
    result = session.scalars(stmt).all()
    return result


def save_answer(session: Session, question_id, answer_text):
    with session as ses:
        question = session.execute(select(Question).where(Question.id ==question_id))
        question = question.scalar_one_or_none()
        if not question:
            return False
        question.answer = answer_text
        question.is_answered = True
        question.answer_at = datetime.now()
        session.commit()
        return True





