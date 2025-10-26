import json
from datadase.models import Product, Category, Costumer
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict, Any


def load_data_from_json(file_path: str) -> Dict[str, Any]:
    """Загружает данные из JSON файла"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def import_data_to_database(session: Session, data: Dict[str, Any]):
    """Импортирует данные в базу данных"""
    # Session = sessionmaker(bind=engine)
    sess = session

    try:
        # Очищаем существующие данные
        sess.query(Product).delete()
        sess.query(Category).delete()

        # Создаем словарь для быстрого поиска категорий по URL
        category_url_to_id = {}

        # Импортируем категории
        print("Импорт категорий...")
        for category_data in data['categories']:
            category = Category(
                name=category_data['name'],
                url=category_data['url'],
                product_count=category_data['product_count']
            )
            session.add(category)
            session.flush()  # Получаем ID категории
            category_url_to_id[category_data['url']] = category.id

        # Импортируем товары
        print("Импорт товаров...")
        for product_data in data['products']:
            # Преобразуем словари в JSON строки
            characteristics_json = json.dumps(product_data.get('characteristics', {}), ensure_ascii=False)
            additional_images_json = json.dumps(product_data.get('additional_images', []), ensure_ascii=False)
            nutrition_facts_json = json.dumps(product_data.get('nutrition_facts', {}), ensure_ascii=False)

            # Получаем ID категории
            category_id = category_url_to_id.get(product_data['category_url'])

            if category_id is None:
                print \
                    (f"Предупреждение: Категория с URL {product_data['category_url']} не найдена для товара {product_data['name']}")
                continue

            product = Product(
                name=product_data['name'],
                url=product_data['url'],
                image=product_data.get('image'),
                price=product_data['price'],
                unit=product_data.get('unit'),
                product_id=product_data['product_id'],
                article=product_data.get('article'),
                description=product_data.get('description'),
                full_description=product_data.get('full_description'),
                characteristics=characteristics_json,
                main_image=product_data.get('main_image'),
                additional_images=additional_images_json,
                weight=product_data.get('weight'),
                calories=product_data.get('calories'),
                nutrition_facts=nutrition_facts_json,
                category_id=category_id
            )
            sess.add(product)

        # Сохраняем изменения
        sess.commit()
        print("Данные успешно импортированы!")

        # Выводим статистику
        category_count = sess.query(Category).count()
        product_count = sess.query(Product).count()
        print(f"Импортировано категорий: {category_count}")
        print(f"Импортировано товаров: {product_count}")

    except Exception as e:
        sess.rollback()
        print(f"Ошибка при импорте данных: {e}")
    finally:
        sess.close()

def test_database_connection(session: Session):
    """Тестирует соединение с базой данных и выводит примеры данных"""
    sess = session

    try:
        # Получаем количество категорий и товаров
        category_count = sess.query(Category).count()
        product_count = sess.query(Product).count()

        print(f"\n=== СТАТИСТИКА БАЗЫ ДАННЫХ ===")
        print(f"Категорий: {category_count}")
        print(f"Товаров: {product_count}")

        # Показываем несколько категорий с количеством товаров
        print(f"\n=== КАТЕГОРИИ ===")
        categories = sess.query(Category).limit(5).all()
        for category in categories:
            product_count_in_category = sess.query(Product).filter(Product.category_id == category.id).count()
            print(f"{category.name}: {product_count_in_category} товаров")

        # Показываем несколько товаров
        print(f"\n=== ПРИМЕРЫ ТОВАРОВ ===")
        products = sess.query(Product).limit(5).all()
        for product in products:
            print(f"{product.name} - {product.price} руб. ({product.category_name})")

    finally:
        sess.close()
