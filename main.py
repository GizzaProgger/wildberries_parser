from browser_factory import get_browser
from Parser import ParserConductor
import os
import json

import pymongo

client = pymongo.MongoClient("mongodb://root:12345678@localhost:27017/")

# проверяем соединение
try:
    # попытаемся отправить ping запрос к серверу
    client.server_info()
    print("Соединение с MongoDB установлено")
except pymongo.errors.ServerSelectionTimeoutError as e:
    # если не удалось установить соединение, выведем ошибку
    print("Не удалось установить соединение с MongoDB: %s" % e)

db_connection = client['wildberies']

browser = get_browser(headless = False)

parser = ParserConductor(browser, db_connection)
parser.re_parse_products('6458da2b9b4a1d5d1837f0dd')
# parser.parse_category_by_id_products_list('6458da2b9b4a1d5d1837f0dd')

# product = parser.parse_product_page("https://www.wildberries.ru/catalog/24695842/detail.aspx")
# print(product)
# parser.parse_categories_products_list()
# parser.parse_categories_products_list('results/categories/all.json')