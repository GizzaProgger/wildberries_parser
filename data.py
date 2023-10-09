from browser_factory import get_browser
from Parser import ParserConductor
import os
import json

import pymongo

from bson.objectid import ObjectId

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

collection = db_connection['products']
documents = collection.find({'category_id': ObjectId('6458da2b9b4a1d5d1837f0dd')})
data = {}
prices = {}
c = 0

sellers = {}

for document in documents:
    price_history = document.get('price_history')
    print(document.get('seller_id'))
    if document['seller_id'] not in sellers:
        sellers[document['seller_id']] = 0
    else:
        sellers[document['seller_id']] += 1
    c += 1
    s = 0
    for price in price_history:
        dt = price['dt']
        if dt not in prices:
            prices[dt] = 0
        else:
            prices[dt] += int(price['price']['RUB'])
    
for dt in prices:
    prices[dt] = prices[dt] / c / 10
# print(json.dumps(prices))

    
# print(sellers)