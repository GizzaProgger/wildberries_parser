import pymongo
from bson.objectid import ObjectId

from serpapi import GoogleSearch

client = pymongo.MongoClient("mongodb://root:12345678@localhost:27017/")
db_connection = client['wildberies']
collection = db_connection['categories']

# Получаем количество документов в коллекции
count = collection.count_documents({})

categories_ids = [
    # ObjectId('6458da2d9b4a1d5d1837f4c2'),
    # ObjectId('6458da2b9b4a1d5d1837f22d'),
    # ObjectId('6458da2b9b4a1d5d1837f0cd'),
    # ObjectId('6458da2b9b4a1d5d1837f1af'),
    # ObjectId('6458d9d79b4a1d5d1837ea7b'),
    # ObjectId('6458da2c9b4a1d5d1837f40b'),
    # ObjectId('6458da2c9b4a1d5d1837f3f5'),
    # ObjectId('6458da309b4a1d5d1837f982'),
    # ObjectId('6458da309b4a1d5d1837f905'),
    # ObjectId('6458da2c9b4a1d5d1837f493'),
    # ObjectId('6458da2d9b4a1d5d1837f512')
]

# Получаем 10 случайных документов
# random_docs = collection.aggregate([{'$sample': {'size': 100}}])

categories = collection.find({"_id": {"$in": categories_ids}})

def process_google_results(data):
    raw_timeseries = data['interest_over_time']['timeline_data']
    timeseries = []
    for raw_item in raw_timeseries:
        item = {
            'date': raw_item['date'],
            'timestamp': raw_item['timestamp'],
            'value': raw_item['values'][0]['extracted_value']
        }
        timeseries.append(item)
    return timeseries

for category in categories:
    query = category.get('seo') or category.get('name')
    print(query)
    params = {
        "engine": "google_trends",
        "q": query,
        "geo": "RU",
        "date": "today 5-y",
        "data_type": "TIMESERIES",
        "api_key": "feb61a45b1cc4e63c33db8250cc81dede8b1ce4456e796bd87cc7acfbc0e3000"
    }
    search = GoogleSearch(params)
    raw_result = search.get_dict()
    print(raw_result)
    db_connection['raw_timeserieses'].insert_one(raw_result)
    db_connection['timeseries'].insert_one({
        'query': query,
        'category_id':  category.get('_id'),
        'series': process_google_results(raw_result)
    })
    print(process_google_results(raw_result))