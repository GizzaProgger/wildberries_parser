import pymongo

import pmdarima as pm
import pandas as pd

client = pymongo.MongoClient("mongodb://root:12345678@localhost:27017/")
db_connection = client['wildberies']
db_timeserieses = db_connection['timeseries']

timeseries_raw = db_timeserieses.find_one()['series']

def transform_data(data):
    # создание пустого списка для хранения преобразованных данных
    transformed_data = []

    # преобразование каждого элемента списка в словарь с ключами 'timestamp' и 'value'
    for d in data:
        transformed_data.append({'timestamp': int(d['timestamp']), 'value': d['value']})

    # создание объекта pandas.DataFrame из преобразованных данных
    df = pd.DataFrame(transformed_data)

    # преобразование столбца 'timestamp' в формат datetime и установка его в качестве индекса
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', inplace=True)

    # переименование столбца 'value' в 'sales'
    df.rename(columns={'value': 'sales'}, inplace=True)

    return df

df = transform_data(timeseries_raw)

# автоматический подбор оптимальных параметров модели
model = pm.auto_arima(df, seasonal=True, m=12)

# вывод оптимальных параметров модели
print(model.order)
print(model.seasonal_order)

# предсказание значений на будущее
forecast = model.predict(n_periods=7)
print(forecast)