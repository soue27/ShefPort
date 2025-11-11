import json

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from datadase.models import Product, Category  # твоя модель


def update_notfound_to_bd(df, session):
    products = []
    df = pd.read_excel("data/filtered.xls", dtype={"Код": str})
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
            description=row.get("Описание", "Отсутсвует описание"),
            full_description=row.get("Описание", "Отсутсвует описание"),
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
    return len(products)


def update_products_from_df(df: pd.DataFrame, session: Session):
    not_found = [] # список артикулов, которых нет в БД
    not_found_rows = []     # строки для отдельного файла

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

    # сохраняем изменения в БД
    session.commit()

    # if len(not_found) > 0:
    #     # Загружаем Excel и сразу читаем столбец "Код" как строку
    #     df = pd.read_excel("data/report.xls", dtype={"Код": str})
    #
    #     # Оставляем только строки с кодами из списка
    #     df_filtered = df[df["Код"].isin(not_found)]
    #
    #     # Сохраняем результат (если нужно)
    #     # df_filtered.to_excel("data/filtered.xlsx", index=False)
    #     dobavka = update_notfound_to_bd(df_filtered, session)

    return f"Не найдено {len(not_found)}"
