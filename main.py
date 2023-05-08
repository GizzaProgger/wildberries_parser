from browser_factory import get_browser
from Parser import ParserConductor
import os
import json

browser = get_browser(headless = True)

parser = ParserConductor(browser)
# parser.parse_categories_products_list('results/categories/all.json')

def save_product_to_db(product):
    # путь к директории для сохранения файла
    dir_path = "./results/products"

    # проверяем, что директория существует
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # путь к файлу для сохранения
    file_path = os.path.join(dir_path, f"{product['name'].replace('/', '-')}.json")

    # сохраняем JSON в файл
    with open(file_path, "w") as f:
        json.dump(product, f, ensure_ascii=False)

parser.parse_products_by_files(save_product_to_db)