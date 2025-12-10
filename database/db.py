"""
Module database.db

This module contains functions for working with database.

It creates a database engine, creates all tables in database and provides a session object for querying database.

It also provides a function for saving user data to database.

"""
import os
import re
from datetime import datetime
from typing import Type, Optional, List, Any

import pandas as pd
from sqlalchemy import select, func, Engine, types, update, delete
from aiogram.types import CallbackQuery
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase, sessionmaker

from data.config import DB_URL, ECHO
from database.models import Base, Costumer, Product, Category, Question, News, Cart, Order, CartItems, AbstractBase, \
    OrderItems
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


def get_all_categories(session: Session, in_stock: bool = False):
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


def get_products_by_category(session: Session, category_id: int, in_stock: bool = False):
    """
    Fetches all products belonging to a specific category.

    :param session: SQLAlchemy session for database operations
    :type session: Session
    :param category_id: ID of the category to filter products by
    :type category_id: int
    :param in_stock: Boolean value indicating whether to filter products by stock
    :type in_stock: bool
    :return: List of Product objects matching the category
    :rtype: list[Product]
    """
    if not in_stock:
        stmt = select(Product).where(Product.category_id == category_id)
    else:
        stmt = select(Product).where(Product.category_id == category_id).where(Product.ostatok > 0)
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
                            Product.characteristics, Product.price).filter(Product.id == product_id).first()
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


def get_costumer_tgid(session: Session, user_id: int):
    """
    Fetches the TG ID of a specific costumer.

    :param session: SQLAlchemy session for database operations
    :param user_id: ID of the costumer to fetch ID for
    :return: ID of the costumer
    """
    stmt = select(Costumer.tg_id).where(Costumer.id == user_id)
    result = session.scalar(stmt)
    return result


def save_question(session: Session, user_id: int, mess_id: int, text: str):
    """
    Saves a question to the database.

    :param session: SQLAlchemy session for database operations
    :param user_id: ТГ ID of the user чей  the question
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
    """
    Retrieve Telegram IDs of all admin users.
    
    Args:
        session: SQLAlchemy session for database operations
        
    Returns:
        list[int]: List of Telegram user IDs for admin users
    """
    stmt = select(Costumer.tg_id).where(Costumer.is_admin == True)
    result = session.scalars(stmt).all()
    return result


def save_answer(session: Session, question_id, answer_text) -> bool:
    question = session.execute(select(Question).where(Question.id == question_id))
    question = question.scalar_one_or_none()
    if not question:
        return False
    question.answer = answer_text
    question.is_answered = True
    question.answer_at = datetime.now()
    session.commit()
    return True


def get_all_costumer_for_mailing(session: Session):
    stmt = select(Costumer.tg_id).where(Costumer.news.is_(True))
    result = session.scalars(stmt).all()
    return result


def save_news(session: Session, data: dict):
    """
    Saves news to the database.

    :param session: SQLAlchemy session for database operations
    :param data -словарь с данными
    """
    for key, value in data.items():
        print(f"{key}: {value}")
    title = data['title']
    post = data['post']
    url = data['url']
    type1 = data['type']
    if 'photo' in data:
        photo = data['photo']
    else:
        photo = None
    with session as ses:
        news = News(title=title, post=post, url=url, image_url=photo, media_type = type1)
        ses.add(news)
        ses.commit()

#regoin

def set_active_entity(session: Session, tg_id: int, model):
    """Установка новой активной корзины"""
    today = datetime.now().strftime("%d.%m.%Y")
    user_id = get_costumer_id(session, tg_id)
    if model == Cart:
        name = f"Корзина от {today}"
    else:
        name = f"Заказ от {today}"
    model=model
    with session as ses:
        entity = model(user_id=user_id, name=name, is_active=True)
        ses.add(entity)
        ses.flush()
        cart_id = entity.id
        ses.commit()
    return cart_id


def save_product_to_entity(session: Session, entity_id: int, product_id: int, quantity: float, unit_price: float, model):
    # Проверяем существующий товар в корзине CartItems, OrderItems
    if model == CartItems:
        existing_item = session.query(CartItems).filter(
            CartItems.cart_id == entity_id,
            CartItems.product_id == product_id
        ).first()
    else:
        existing_item = session.query(OrderItems).filter(
            OrderItems.order_id == entity_id,
            OrderItems.product_id == product_id
        ).first()

    if existing_item:
        existing_item.quantity += quantity
    elif model == CartItems: # Tсли товара нет, то создаем новую запись
        item = model(
            cart_id=entity_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        )
        session.add(item)
    else:
        item = model(
            order_id=entity_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        )
        session.add(item)
    session.commit()
    return True


def get_active_entity(session: Session, user_id: int, model):
    """Возвращает активную корзину пользователя"""
    id = get_costumer_id(session, user_id)
    stmt = select(model).where(
        model.user_id == id,
        model.is_active == True
    )
    result = session.execute(stmt)
    return result.scalars().first()


def get_entity_items(session: Session, cart_id: int, model):
    """Возвращает список товаров корзины CartItems, OrderItems"""
    if model == CartItems:
        stmt = select(model).where(CartItems.cart_id == cart_id)
    else:
        stmt = select(model).where(OrderItems.order_id == cart_id)
    return session.execute(stmt).scalars().all()


def change_item_quantity(session: Session, item_id: int, delta: int, model):
    """Изменяет количество товара CartItems, OrderItems"""
    stmt = select(model).where(model.id == item_id)
    item = session.execute(stmt).scalar_one_or_none()

    if not item:
        return None

    item.quantity = max(1, item.quantity + delta)
    session.commit()
    session.refresh(item)
    return item


def delete_entity_item(session: Session, item_id: int, model):
    """Удаляет элемент корзины CartItems, OrderItems"""
    stmt = delete(model).where(model.id == item_id)
    session.execute(stmt)
    session.commit()


def confirm_entity(session: Session, cart_id: int, model):
    """Подтверждение корзины Cart Order"""
    stmt = (
        update(model)
        .where(model.id == cart_id)
        .values(is_active=False, is_done=True)
    )
    session.execute(stmt)
    session.commit()
    return session.get(model, cart_id)


def delete_entity(session: Session, item_id: int, model):
    """Удаляет  корзину Cart, Order"""
    stmt = delete(model).where(model.id == item_id)
    session.execute(stmt)
    session.commit()


def get_entity_item(session: Session, item_id: int, model):
    """Получение элемента корзины CartItems, OrderItems"""
    stmt = select(model).where(model.id == item_id)
    result = session.execute(stmt).scalar_one_or_none()  # Получаем один объект или None
    return result


def get_entity_by_id(session: Session, item_id: int, model):
    """Получение элемента корзины Cart, Order"""
    stmt = select(model).where(model.id == item_id)
    result = session.execute(stmt).scalar_one_or_none()  # Получаем один объект или None
    return result


def get_entity_for_done(session: Session, model):
    """Получение элемента корзины Cart, Order для подготовки"""
    stmt = select(model).where(model.is_done == True).order_by(model.id)
    result = session.scalars(stmt).all()
    return result


def set_entity_for_issue(session: Session, entity_id, model):
    """Устанавливает признак готовности Cart, Order для выдачи товара"""
    stmt = (
        update(model)
            .where(model.id == entity_id)
            .values(is_done=False, is_issued=True, is_done_at=datetime.now())
        ).returning(model)
    result = session.execute(stmt)
    updated_entity = result.scalar_one_or_none()
    session.commit()
    return updated_entity


def get_entity_for_issued(session: Session, model):
    """Получение элемента корзины Cart, Order для подготовки"""
    stmt = select(model).where(model.is_issued == True).order_by(model.id)
    result = session.scalars(stmt).all()
    return result


def set_entity_close(session: Session, id, model):
    """Закрывает корзину Cart, Order после выдачи товара"""
    stmt = update(model).where(model.id == id).values(is_issued=False, is_issued_at=datetime.now())
    session.execute(stmt)
    session.commit()
    return session.get(model, id)


def get_entity_by_user_id(session: Session, user_id: int, model):
    """поолучение всех неактивных корзин по айди пользователя"""
    stmt = select(model).where(model.user_id==user_id,
                               model.is_active==False).order_by(model.id)
    result = session.scalars(stmt).all()
    return result



##########################################
#раздел работы с корзиной покупок и заказов
##########################################
#endregoin


def load_data(file_name: str, engine: Engine) -> int:
    """Загрузка новых товаров в БД"""
    try:
        df = pd.read_excel(file_name, dtype={"article": str})
        dtype_config = {
            "name" : types.String(500),
            "url" : types.String(500),
            "image" : types.String(500),
            "price" : types.Float(),
            "unit" : types.String(50),
            "product_id" : types.String(100),
            "article" : types.String(100),
            "description" : types.Text,
            'full_description' : types.Text,
            "characteristics" : types.Text,
            "main_image" : types.String(500),
            "additional_images" : types.Text,
            "weight" : types.String(100),
            "calories" : types.String(100),
            "nutrition_facts" : types.Text,
            "category_id" : types.Integer(),
            "ostatok" :types.Float()
        }

        df.to_sql(name='products', con=engine, if_exists='append', index=False, dtype=dtype_config)
        result = df.shape[0]
        os.remove(file_name)
        del df
        return result
    except Exception as e:
        os.remove(file_name)
        print(e)
        del df
        return 0


def get_product_by_id(session: Session, product_id: int):
    """
    Get product by id from database.

    :param session: session object of SQLAlchemy
    :param product_id: id of product in database
    :return: product object or None if product not found
    """
    with session as ses:
        stmt = select(Product).where(Product.id == product_id)
        result = session.scalar(stmt)
        return result





