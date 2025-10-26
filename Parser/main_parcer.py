import time
from datetime import datetime
from detail import parse_product_details_chefport, enhance_products_with_details_chefport
from parser import get_categories_requests, parse_products_from_category, save_products_to_json, save_products_to_csv, \
    create_complete_catalog_json, save_catalog_to_json

if __name__ == '__main__':
    """Основная функция парсинга"""
    print("🚀 Запуск парсера ChefPort...")

    # 1. Парсим категории
    categories = get_categories_requests()
    print(categories)

    # 2. Парсим товары для каждой категории
    all_products = []

    for category in categories:
        print(f"\n📦 Парсим категорию: {category['name']}")

        # Парсим базовые данные товаров
        products = parse_products_from_category(category['url'])
        print(f"  ✅ Найдено товаров: {len(products)}")

        # Добавляем информацию о категории
        for product in products:
            product['category_url'] = category['url']
            product['category_name'] = category['name']

        # Парсим детальную информацию
        print(f"  🔍 Собираем детальную информацию...")
        enhanced_products = enhance_products_with_details_chefport(products)

        all_products.extend(enhanced_products)
        print(f"  ✅ Обработано товаров: {len(enhanced_products)}")

        time.sleep(2)  # Задержка между категориями


    # 3. Формируем JSON
    print(f"\n📊 Формируем итоговый каталог...")
    catalog = create_complete_catalog_json(categories, all_products)

    # 4. Сохраняем
    filename = save_catalog_to_json(catalog)

    # Статистика
    print(f"\n🎉 Парсинг завершен!")
    print(f"📈 Итоговая статистика:")
    print(f"   • Категорий: {len(categories)}")
    print(f"   • Товаров: {len(all_products)}")
    print(f"   • Файл: {filename}")
