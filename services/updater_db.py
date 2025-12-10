"""
Module for updating database with data from report.xls.

Functions:
    update_products_from_df(df: pd.DataFrame, session: Session) -> None:
        Updates products in database with data from DataFrame.

    load_report(path: str = "data/report.xls") -> pd.DataFrame:
        Loads report from file and returns DataFrame.

"""
import json

import pandas as pd
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import Product, Category  # твоя модель


def load_report(path: str = "data/report.xls") -> pd.DataFrame:
    """Loads report from file and returns DataFrame.
    Args:
        path (str): Path to report file.
    Returns:
        pd.DataFrame: DataFrame with report data.
    """
    # Загружаем только нужные столбцы
    usecols = ["Код", "Цена продажи", "Количество"]
    df = pd.read_excel(path, usecols=usecols, dtype={"Код": str})
    # Приводим поля "Код" и "Артикул" к строке
    df["Код"] = df["Код"].astype(str).str.strip()
    # Чистим типы
    df["Цена продажи"] = pd.to_numeric(df["Цена продажи"], errors="coerce").fillna(0)
    df["Количество"] = pd.to_numeric(df["Количество"], errors="coerce").fillna(0)
    logger.info(f"загружено из файла {df.shape[0]} строк")
    return df


def update_notfound_to_bd(df, session):
    """Converts the "Количество" column to numeric values or sets it to 0 if conversion fails.
     Args:
        df (pd.DataFrame): DataFrame containing the "Количество" column.
        session (Session): SQLAlchemy session for database operations.
    Returns:
        pd.DataFrame: DataFrame with the "Количество" column converted to numeric values or set to 0.
    """
    products = []
    for _, row in df.iterrows():
        product = Product(
            category_id=int(row.get("Категория")),
            name=row.get("Наименование", "No name"),
            url=row.get("url", "https://chefport.ru/catalog"),
            image=row.get(""),
            price=float(row.get("Цена продажи", 0)),
            unit=row.get("Единица измерения"),
            product_id=str(row.get("Код")),  # обязательно str, ведущие нули сохранятся
            article=str(row.get("Код")),
            description=row.get("Описание", "Отсутствует описание"),
            full_description=row.get("Описание", "Отсутствует описание"),
            characteristics=json.dumps(row.get("Характеристики")) if row.get("Характеристики") else None,
            main_image=row.get(""),
            additional_images=json.dumps(row.get("Доп. изображения")) if row.get("Доп. изображения") else None,
            weight=row.get("Вес"),
            calories=row.get("Калории"),
            nutrition_facts=json.dumps(row.get("Пищевая ценность")) if row.get("Пищевая ценность") else None,
            ostatok=row.get("Количество", 0)
            )
        products.append(product)

    session.add_all(products)
    session.commit()
    logger.info(f"В БД добавлено {len(products)} товаров")
    return len(products)


def update_products_from_df(df: pd.DataFrame, session: Session):

    not_found = [] # список артикулов, которых нет в БД
    not_found_rows = []     # строки для отдельного файла
    count = 0

    for _, row in df.iterrows():
        kod = str(row["Код"])
        price = float(row["Цена продажи"])
        ostatok = float(row["Количество"])

        stmt = select(Product).where(Product.article == kod)
        product = session.scalars(stmt).first()

        if product is None:
            not_found.append(kod)
            not_found_rows.append(row)
            continue

        # обновляем данные
        product.price = price
        product.ostatok = ostatok
        count += 1

    # сохраняем изменения в БД
    session.commit()
    logger.info(f"В БД обновлено {count} товаров")

    if len(not_found) > 0:
        # Загружаем Excel и сразу читаем столбец "Код" как строку
        df = pd.read_excel("data/report.xls", dtype={"Код": str})

        # Оставляем только строки с кодами из списка
        df_filtered = df[df["Код"].isin(not_found)]

        # Сохраняем результат (если нужно)
        df_filtered.to_excel("data/output.xlsx", engine='openpyxl', index=False)
        # dobavka = update_notfound_to_bd(df_filtered, session)
        logger.info(f"Необхоидмо добавление {df_filtered.shape[0]} товаров")
    else:
        logger.info(f"Добавление товаров не требуется")
    return len(not_found)
