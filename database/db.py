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
from aiogram.types import CallbackQuery
from loguru import logger
from sqlalchemy import MetaData, Table, case
from sqlalchemy import create_engine
from sqlalchemy import select, func, update, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy.util import ellipses_string

from data.config import DB_URL
from database.models import Base, Costumer, Product, Category, Question, News, Cart, CartItems, OrderItems
from services.search import normalize_text

engine = create_engine(DB_URL,
                       poolclass=QueuePool,
                       pool_size=5,  # минимальное количество соединений
                       max_overflow=10,  # максимальное количество соединений
                       pool_timeout=30,  # тайм-аут ожидания (сек)
                       pool_recycle=1800,  # пересоздавать каждые 30 минут
                       pool_pre_ping=True,  # проверять перед использованием

                       # Настройки подключения psycopg2
                       connect_args={
                           'connect_timeout': 10,
                           'application_name': 'my_app',
                           'keepalives': 1,
                           'keepalives_idle': 30,
                           'keepalives_interval': 10,
                           'keepalives_count': 5
                       },

                       # Другие настройки
                       echo=False,  # логировать SQL запросы
                       echo_pool=False,  # логировать операции пула
                       execution_options={
                           'isolation_level': 'READ COMMITTED'
                       }
                       )
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
        costumer = Costumer(
            tg_id=user_id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            news=news
            )
        session.add(costumer)
    else:
        costumer.news = news
        costumer.updated_at = datetime.now()
    # session.commit()


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
        stmt = select(Product).where(Product.category_id == category_id).where(Product.ostatok > 0.05)
    result = session.scalars(stmt).all()
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
    stmt = (
        select(Product)
        .order_by(
            case(
                (Product.ostatok > 0.05, 1),
                else_=0
            ).desc()
        )
    )
    products = session.scalars(stmt).all()
    for product in products:
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
    product = session.query(Product.name, Product.image, Product.description,
                            Product.characteristics, Product.price).filter(Product.id == product_id).first()
    return product


def get_product_by_article(session: Session, article: str):
    """Выборка товара по его артиклю"""
    product = session.query(Product).filter(Product.article == article).first()
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
    question = Question(user_id=user_id, questions_id=mess_id, text=text)
    session.add(question)
    # session.commit()


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


def set_admin(session: Session, admin_tg_id: int, to_delete: bool):
    admin = session.query(Costumer).filter(Costumer.tg_id == admin_tg_id).one_or_none()
    if to_delete:
        admin.is_admin = False
    else:
        admin.is_admin = True
    # session.commit()


def save_answer(session: Session, question_id, answer_text) -> bool:
    question = session.execute(select(Question).where(Question.id == question_id))
    question = question.scalar_one_or_none()
    if not question:
        return False
    question.answer = answer_text
    question.is_answered = True
    question.answer_at = datetime.now()
    # session.commit()
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
    title = data['title']
    post = data['post']
    url = data['url']
    type1 = data['type']
    if 'photo' in data:
        photo = data['photo']
    else:
        photo = None
    news = News(title=title, post=post, url=url, image_url=photo, media_type=type1)
    session.add(news)
    # session.commit()


# regoin

def set_active_entity(session: Session, tg_id: int, model):
    """Установка новой активной корзины"""
    today = datetime.now().strftime("%d.%m.%Y")
    user_id = get_costumer_id(session, tg_id)
    if model == Cart:
        name = f"Корзина от {today}"
    else:
        name = f"Заказ от {today}"
    model = model
    entity = model(user_id=user_id, name=name, is_active=True)
    session.add(entity)
    session.flush()
    cart_id = entity.id
    # session.commit()
    return cart_id


def save_product_to_entity(session: Session, entity_id: int, product_id: int, quantity: float, unit_price: float,
                           model):
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
    elif model == CartItems:  # Tсли товара нет, то создаем новую запись
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
    # session.commit()
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
    # session.commit()
    session.refresh(item)
    return item


def delete_entity_item(session: Session, item_id: int, model):
    """Удаляет элемент корзины CartItems, OrderItems"""
    stmt = delete(model).where(model.id == item_id)
    session.execute(stmt)
    # session.commit()


def confirm_entity(session: Session, cart_id: int, model):
    """Подтверждение корзины Cart Order"""
    stmt = (
        update(model)
        .where(model.id == cart_id)
        .values(is_active=False, is_done=True)
    )
    session.execute(stmt)
    # session.commit()
    return session.get(model, cart_id)


def delete_entity(session: Session, item_id: int, model):
    """Удаляет  корзину Cart, Order"""
    print(model)
    if model is Cart:
        stmt = delete(CartItems).where(CartItems.cart_id == item_id)
    else:
        stmt = delete(OrderItems).where(OrderItems.order_id == item_id)
    session.execute(stmt)
    stmt = delete(model).where(model.id == item_id)
    session.execute(stmt)
    # session.commit()


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
    # session.commit()
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
    # session.commit()
    return session.get(model, id)


def get_entity_by_user_id(session: Session, user_id: int, model):
    """поолучение всех неактивных корзин по айди пользователя"""
    stmt = select(model).where(model.user_id == user_id,
                               model.is_active == False).order_by(model.id)
    result = session.scalars(stmt).all()
    return result


##########################################
# раздел работы с корзиной покупок и заказов
##########################################
# endregoin


def load_data(file_name: str, engine: Engine) -> int:
    """Загрузка новых товаров обновление товаров в БД"""
    try:
        logger.info(f"Начало загрузки файла {file_name}")

        # 1. Чтение файла
        df = pd.read_excel(file_name, dtype={"article": str})
        df = df.drop(columns=["id"], errors="ignore")

        # 2. NaN -> None
        df = df.where(pd.notnull(df), None)

        if df.empty:
            logger.exception(f"Файл %s пуст {file_name}")
            return 0

        metadata = MetaData()
        products = Table("products", metadata, autoload_with=engine)

        # 3. Получаем существующие артикли
        with engine.begin() as conn:
            existing_articles = {
                row[0]
                for row in conn.execute(
                    select(products.c.article)
                )
                if row[0] is not None
            }

        # 4. Делим данные
        is_duplicate = df["article"].isin(existing_articles)

        df_duplicates = df[is_duplicate]
        df_new = df[~is_duplicate]

        # 5. Логируем дубли
        if not df_duplicates.empty:
            logger.exception(f"Найдено {len(df_duplicates)} дублей по article")
            for _, row in df_duplicates.iterrows():
                logger.exception(f"Дубль {row.get("article")} {row.get("name")} {row.get("price")}")

        # 6. Вставка новых
        if df_new.empty:
            logger.info("Новых товаров для вставки нет")
            return 0

        rows = df_new.to_dict(orient="records")

        with engine.begin() as conn:
            conn.execute(insert(products), rows)

        logger.info(f"Загружено {len(df_new)} новых товаров, пропущено {len(df_duplicates)} дублей")

        return len(df_new)

    except Exception as e:
        logger.exception(f"Ошибка загрузки файла {file_name}")
        return 0

    finally:
        if os.path.exists(file_name):
            os.remove(file_name)


def get_product_by_id(session: Session, product_id: int):
    """
    Get product by id from database.

    :param session: session object of SQLAlchemy
    :param product_id: id of product in database
    :return: product object or None if product not found
    """
    stmt = select(Product).where(Product.id == product_id)
    result = session.scalar(stmt)
    return result


def delete_product_by_id(session: Session, product_id: int) -> bool:
    product = session.get(Product, product_id)
    if not product:
        return False
    session.delete(product)
    # session.commit()
    return True


# ********************
# Analitics
# ********************

def get_all_tables_names():
    """Динамическое получение всех моделей БД для формирования выгрузок"""
    return Base.metadata.tables.keys()


def clean_excel_string(s: str) -> str:
    """Удаляет неподдерживаемые Excel символы из строки."""
    if not isinstance(s, str):
        return s
    # Убираем все control characters кроме \t и \n
    return re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", s)


def export_data_to_excel(session: Session, table_name: str, file_path: str):
    """ Load new products data to database.
        :param:
            file_name (str): Path to Excel file with products data.
            engine (sqlalchemy.engine.Engine): SQLAlchemy engine instance.

    """
    table = Base.metadata.tables.get(table_name)
    print(table)
    # if not table:
    #     raise ValueError(f"Таблица {table_name} не найдена")
    # Выполняем SELECT
    result = session.execute(table.select())
    df = pd.DataFrame(result.fetchall(), columns=result.keys())

    for col in df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
        df[col] = df[col].dt.tz_localize(None)

    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(clean_excel_string)
    # Сохраняем в Excel
    df.to_excel(file_path, index=False)


def entity_to_excel(entity):
    """Выгружает любую сущность из моделей в ексель, но только одну
    для загрузки нескольких использовать:
    products = session.query(Product).all()
    df = pd.DataFrame([orm_to_dict(p) for p in products])
    df.to_excel("products.xlsx", index=False)
    """
    entity_dict = {c.key: getattr(entity, c.key) for c in inspect(entity).mapper.column_attrs}
    df = pd.DataFrame([entity_dict])
    for col in df.select_dtypes(include=['datetime64[ns, UTC]']).columns:  # Убирает тайм зону из столбцов с датами.
        df[col] = df[col].dt.tz_localize(None)
    file_name = f"data/Инфа_{entity_dict.get('article')}.xlsx"
    df.to_excel(file_name, index=False)
    return file_name


def update_prooduct_field(session: Session, product_id, field, value):
    product = session.get(Product, product_id)
    if not product:
        raise ValueError("Товар не найден")
    print(product_id, field, value)
    match field:
        case "name":
            product.name = value
        case "price":
            product.price = float(value)
        case "ostatok":
            product.ostatok = float(value)
        case "unit":
            product.unit = value
        case "description":
            product.description = value
        case "image":
            product.main_image = value
        case _:
            raise ValueError("Неизвестное поле")
    #session.commit()
