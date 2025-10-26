from datetime import datetime

import requests
from bs4 import BeautifulSoup
import json
import time
import json
import csv
from urllib.parse import urljoin

def get_categories_requests():
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    response = requests.get("https://chefport.ru/catalog", headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

        # Ищем навигационное меню
    nav = soup.find('ul', class_='b-catalog-nav')

    categories = []
    if nav:
            # Извлекаем все элементы списка
        items = nav.find_all('li', class_='b-catalog-nav__item')

        for item in items:
            link = item.find('a', class_='b-catalog-nav__item-link')
            if link:
                name = link.get_text(strip=True)
                url = link.get('href')
                categories.append({
                        'name': name,
                        'url': url
                })

    return categories


def parse_products_from_category(base_url):
    """
    Парсит все товары из категории с учетом пагинации
    """
    all_products = []
    page = 1

    while True:
        # Формируем URL страницы (может быть с параметром page или изменяться по-другому)
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}?page={page}"  # или другой формат пагинации
            # https: // chefport.ru / catalog / moreproduktyi?page = 2

        print(f"Парсим страницу {page}: {url}")
        print(url)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Парсим товары с текущей страницы
            products = parse_products_from_page(soup, base_url)

            if not products:
                print("Товары не найдены, завершаем парсинг")
                break

            all_products.extend(products)
            print(f"Найдено товаров на странице: {len(products)}")

            # Проверяем наличие следующей страницы
            # if not has_next_page(soup):
            #     print("Это последняя страница")
            #     break

            page += 1
            time.sleep(1)  # Задержка между запросами

        except requests.RequestException as e:
            print(f"Ошибка при запросе страницы {page}: {e}")
            break

    return all_products


def parse_products_from_page(soup, base_url):
    """
    Парсит товары с одной страницы
    """
    products = []

    # Ищем все карточки товаров
    product_items = soup.find_all('div', class_='b-product-item')

    for item in product_items:
        try:
            product_data = {}

            # Название товара
            title_element = item.find('h3', class_='b-product-item__information-title')
            if title_element:
                product_data['name'] = title_element.get_text(strip=True)
            else:
                product_data['name'] = None

            # Ссылка на товар
            link_element = item.find('a', class_='b-product-item__image')
            if link_element and link_element.get('href'):
                product_data['url'] = urljoin(base_url, link_element.get('href'))
            else:
                # Пробуем найти ссылку в заголовке
                title_link = item.find('a', href=True)
                if title_link:
                    product_data['url'] = urljoin(base_url, title_link.get('href'))
                else:
                    product_data['url'] = None

            # Изображение
            img_element = item.find('img', class_='img-fluid')
            if img_element and img_element.get('src'):
                product_data['image'] = urljoin(base_url, img_element.get('src'))
                product_data['image_alt'] = img_element.get('alt', '')
            else:
                product_data['image'] = None
                product_data['image_alt'] = ''

            # Цена
            price_element = item.find('div', class_='b-product-item-price__current')
            if price_element:
                price_text = price_element.get_text(strip=True)
                # Извлекаем только цифры из цены
                product_data['price'] = extract_price(price_text)
            else:
                product_data['price'] = None

            # Единица измерения
            unit_element = item.find('div', class_='b-product-item-price__unit')
            if unit_element:
                product_data['unit'] = unit_element.get_text(strip=True).replace('за\xa0', '')
            else:
                product_data['unit'] = 'шт.'  # значение по умолчанию

            # Дополнительная информация
            product_id_element = item.find('input', {'name': 'product_id'})
            if product_id_element:
                product_data['product_id'] = product_id_element.get('value')
            else:
                product_data['product_id'] = None

            # Общая стоимость (если есть)
            total_price_element = item.find('span', class_='totalPrice')
            if total_price_element:
                product_data['total_price'] = total_price_element.get_text(strip=True)
            else:
                product_data['total_price'] = None

            products.append(product_data)

        except Exception as e:
            print(f"Ошибка при парсинге товара: {e}")
            continue

    return products


def extract_price(price_text):
    """
    Извлекает числовое значение цены из текста
    """
    try:
        # Убираем все нецифровые символы, кроме точек и запятых
        cleaned = ''.join(c for c in price_text if c.isdigit() or c in ',.')
        # Заменяем запятую на точку для преобразования в float
        cleaned = cleaned.replace(',', '.').replace(' ', '')
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


def has_next_page(soup):
    """
    Проверяет наличие следующей страницы
    """
    # Ищем элементы пагинации
    next_button = soup.find('a', string=['>', 'Далее', 'Next'])
    if next_button and next_button.get('href'):
        return True

    # Ищем активную страницу и следующую за ней
    current_page = soup.find('li', class_=lambda x: x and 'active' in x)
    if current_page:
        next_page = current_page.find_next_sibling('li')
        if next_page and next_page.find('a'):
            return True

    # Проверяем наличие пагинационного контейнера
    pagination = soup.find('ul', class_=lambda x: x and 'pagination' in x.lower())
    if pagination:
        pages = pagination.find_all('a')
        return len(pages) > 1

    return False


def save_products_to_csv(products, filename='oysters_products.csv'):
    """
    Сохраняет список товаров в CSV файл

    Args:
        products (list): Список словарей с данными товаров
        filename (str): Название файла для сохранения
    """
    if not products:
        print("Нет данных для сохранения")
        return

    # Определяем все возможные поля из данных
    fieldnames = set()
    for product in products:
        fieldnames.update(product.keys())

    # Преобразуем в список для сохранения порядка
    fieldnames = list(fieldnames)

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for product in products:
            writer.writerow(product)

    print(f"Сохранено {len(products)} товаров в файл {filename}")


def save_products_to_json(products, filename='moreproduktyi_products.json'):
    """
    Сохраняет товары в JSON файл
    """
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(products, file, ensure_ascii=False, indent=2)

    print(f"Сохранено {len(products)} товаров в файл {filename}")


def create_complete_catalog_json(categories, products):
    """Создает полный JSON каталог"""

    # Добавляем счетчики товаров в категории
    for category in categories:
        category_products = [p for p in products if p.get('url') == category['url']]
        category['product_count'] = len(category_products)

    catalog = {
        "metadata": {
            "source": "chefport.ru",
            "total_categories": len(categories),
            "total_products": len(products),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        },
        "categories": categories,
        "products": products
    }

    return catalog


def save_catalog_to_json(catalog, filename=None):
    """Сохраняет каталог в JSON файл"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chefport_catalog_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"💾 Каталог сохранен в файл: {filename}")
    return filename