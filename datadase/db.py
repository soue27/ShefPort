"""
Module datadase.db

This module contains functions for working with database.

It creates a database engine, creates all tables in database and provides a session object for querying database.

It also provides a function for saving user data to database.

"""
from datetime import datetime

from aiogram.types import Message, CallbackQuery
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from data.config import DB_URL, ECHO
from datadase.models import Base, Costumer, Cart, CartItems, Product, Category

print(DB_URL)
engine = create_engine(DB_URL, echo=ECHO)
Base.metadata.create_all(engine)
session = Session(engine)
connect = engine.connect()


def save_costumer(session: Session, callback: CallbackQuery, news: bool):
    """
    Saves user data to database.

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






