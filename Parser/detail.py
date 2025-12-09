import requests
from bs4 import BeautifulSoup
import time
import json
import csv
from urllib.parse import urljoin
import re
from loguru import logger


def parse_product_details_chefport(product_url):
    """
    Парсит детальную информацию о товаре со страницы товара на chefport.ru
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    }

    try:
        response = requests.get(product_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        details = {
            'article': '',
            'description': '',
            'full_description': '',
            'characteristics': {},
            'main_image': '',
            'additional_images': [],
            'weight': '',
            'calories': '',
            'nutrition_facts': {}
        }

        # 1. АРТИКУЛ - из элемента с классом p-product__code
        article_element = soup.find('p', class_='p-product__code')
        if article_element:
            article_text = article_element.get_text(strip=True)
            # Извлекаем артикул (цифры после "Артикульный номер:")
            article_match = re.search(r'Артикульный номер:\s*([^\s]+)', article_text)
            if article_match:
                details['article'] = article_match.group(1)
            else:
                # Альтернативно: ищем любые цифры в тексте
                numbers = re.findall(r'\d+', article_text)
                if numbers:
                    details['article'] = numbers[0]

        # 2. ОСНОВНОЕ ИЗОБРАЖЕНИЕ
        main_img_element = soup.find('a', class_='p-product__image-img')
        if main_img_element and main_img_element.get('href'):
            details['main_image'] = urljoin(product_url, main_img_element.get('href'))
        else:
            # Ищем в теге img
            img_element = soup.find('img', src=True)
            if img_element:
                details['main_image'] = urljoin(product_url, img_element.get('src'))

        # 3. ДОПОЛНИТЕЛЬНЫЕ ИЗОБРАЖЕНИЯ
        additional_images_container = soup.find('div', class_='p-product__image-additional')
        if additional_images_container:
            additional_links = additional_images_container.find_all('a', href=True)
            for link in additional_links:
                img_url = urljoin(product_url, link.get('href'))
                if img_url not in details['additional_images']:
                    details['additional_images'].append(img_url)

        # 4. ОПИСАНИЕ - из блока с классом p-product__right-text
        description_element = soup.find('div', class_='p-product__right-text')
        if description_element:
            # Извлекаем весь текст описания
            description_text = description_element.get_text(strip=True)
            details['description'] = description_text

            # Также сохраняем HTML описание (очищенное)
            desc_html = description_element.decode_contents()
            details['full_description'] = re.sub(r'\s+', ' ', desc_html).strip()

        # 5. ХАРАКТЕРИСТИКИ - из блока b-attribute
        characteristics_element = soup.find('div', class_='b-attribute')
        if characteristics_element:
            characteristics_items = characteristics_element.find_all('div', class_='attribute-item')

            for item in characteristics_items:
                name_element = item.find('div', class_='attribute-item__name')
                value_element = item.find('div', class_='attribute-item__value')

                if name_element and value_element:
                    name = name_element.get_text(strip=True)
                    value = value_element.get_text(strip=True)
                    details['characteristics'][name] = value

                    # Извлекаем специфичные характеристики
                    if 'калорийность' in name.lower():
                        details['calories'] = value
                    if 'вес' in name.lower() or 'масса' in name.lower():
                        details['weight'] = value

        # 6. ПИТАТЕЛЬНАЯ ЦЕННОСТЬ - из описания
        nutrition_patterns = {
            'белки': r'белки[:\s]*([\d.,]+)\s*г',
            'жиры': r'жиры[:\s]*([\d.,]+)\s*г',
            'углеводы': r'углеводы[:\s]*([\d.,]+)\s*г',
            'калории': r'калорийность[^\d]*([\d.,]+)\s*ккал'
        }

        description_text = details['description']
        for key, pattern in nutrition_patterns.items():
            match = re.search(pattern, description_text.lower())
            if match:
                details['nutrition_facts'][key] = match.group(1)

        # 7. ВЕС ТОВАРА - пытаемся извлечь из названия
        weight_match = re.search(r'(\d+)\s*(г|кг|мл|л)', details.get('name', ''))
        if weight_match:
            details['weight'] = f"{weight_match.group(1)} {weight_match.group(2)}"

        print(f"✓ Собраны детали для: {product_url}")
        return details

    except Exception as e:
        logger.exception(f"✗ Ошибка при парсинге {product_url}: {e}")
        return None


def enhance_products_with_details_chefport(products, delay=1):
    """
    Обогащает список товаров детальной информацией для chefport.ru
    """
    enhanced_products = []

    for i, product in enumerate(products):
        print(f"Обрабатываем товар {i + 1}/{len(products)}: {product.get('name', 'Без названия')}")

        if product.get('url'):
            details = parse_product_details_chefport(product['url'])

            if details:
                # Объединяем основную и детальную информацию
                enhanced_product = {**product, **details}
                enhanced_products.append(enhanced_product)
            else:
                # Если не удалось собрать детали, оставляем исходные данные
                enhanced_products.append(product)
        else:
            enhanced_products.append(product)

        # Задержка между запросами
        time.sleep(delay)

    return enhanced_products


def save_enhanced_products_to_csv_chefport(products, filename='chefport_products_enhanced.csv'):
    """
    Сохраняет обогащенные товары в CSV с учетом новой структуры
    """
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = [
            'name', 'price', 'unit', 'url', 'image', 'product_id', 'total_price',
            'article', 'description', 'weight', 'calories', 'main_image'
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for product in products:
            writer.writerow(product)

    print(f"Сохранено {len(products)} обогащенных товаров в {filename}")


def save_detailed_products_to_json(products, filename='chefport_products_detailed.json'):
    """
    Сохраняет полную информацию о товарах в JSON
    """
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(products, file, ensure_ascii=False, indent=2)

    print(f"Сохранено {len(products)} товаров с полной информацией в {filename}")
