import os 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup

import json
import re

import time

from loguru import logger
import datetime

import requests

from bson.objectid import ObjectId

class Parser:

    def __init__(self, browser):
        self.browser = browser
    
    def end(self):
        self.browser.quit()

    def save_html_page(self, url, filename):
        # Загружаем страницу
        self.browser.get(url)

        # Получаем исходный код страницы
        page_source = self.browser.page_source

        self.save_to_file(page_source, filename)
    
    def parse_categories(self):
        response = requests.get("https://static-basket-01.wb.ru/vol0/data/main-menu-ru-ru-v2.json")
        if response.status_code == 200:
            return response.json()
        return []

    def parse_products_list(self, items_list_url, filepath):
        data = {
            'meta': {},
            'products': {}
        }
        # Открыть страницу
        print(items_list_url)
        self.browser.get(items_list_url)
        WebDriverWait(self.browser, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.catalog-page__main')))
        
        # # Пролистать страницу до конца, пока не перестанут появляться новые товары
        while True:
            # Получить высоту страницы перед прокруткой
            last_height = self.browser.execute_script("return document.body.scrollHeight")
            
            # Прокрутить страницу до конца
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Добавить небольшую задержку, чтобы страница успела загрузиться
            time.sleep(2)
            
            # Получить высоту страницы после прокрутки
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            # Если высота не изменилась, значит, все товары загружены, можно выйти из цикла
            if new_height == last_height:
                break
        
        # Получить HTML-код страницы
        html = self.browser.page_source
        
        # Создать объект BeautifulSoup для парсинга HTML-кода
        soup = BeautifulSoup(html, 'html.parser')
        
        breadcrumbs = {}
        breadcrumbs_elements = soup.select(".breadcrumbs__link")
        for element in breadcrumbs_elements:
            breadcrumbs[element.get("href")] = element.text.strip()

        category_name = soup.select_one(".breadcrumbs__item:last-of-type span").text

        span_element = soup.select_one('span[data-link*="pagerModel.totalItems"]')
        if span_element is not None:
            number_with_spaces = span_element.text.strip()
            product_number = int(re.sub('[^0-9]', '', number_with_spaces))
            
        else:
            product_number = None

        meta = {
            'breadcrumbs': breadcrumbs,
            'category_name': category_name,
            'product_number': product_number
        }

        data['meta'] = meta

        cards = {}
        s = soup.select(".product-card__wrapper")
        for i in range(len(s)):
            card = s[i]
            # Получить название товара
            name = card.select_one('h2').text.strip()
            
            # Получить цену товара
            price = card.select_one('.price__lower-price').text.strip()
            
            # Получить скидку на товар, если есть
            discount = card.select_one('del')
            if discount:
                discount = re.sub('[^0-9]', '', discount.text.strip())
            else:
                discount = price
            
            # Добавить информацию о товаре в словарь cards под ключем из поля .product-card__wrapper .product-card__link
            link = card.select_one('a.product-card__link')['href']

            rating = soup.select_one('.address-rate-mini').text.strip()

            count = card.select_one('.product-card__count').text

            cards[link] = {
                'name': name,
                'price': int(re.sub('[^0-9]', '', price)),
                'discount': int(re.sub('[^0-9]', '', discount)),
                'rating': rating,
                'count': int(re.sub('[^0-9]', '', count)),
                'index': i
            }
        
        data['products'] = cards

        self.save_to_file(
            json.dumps(data, ensure_ascii=False).replace("https://www.wildberries.ru", ""),
            filepath
        )

        return data

    def parse_product_page(self, url):
        self.browser.get(url)
        try:
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'product-page__header'))
            WebDriverWait(self.browser, timeout=10).until(element_present)
            
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'tooltip__content'))
            WebDriverWait(self.browser, timeout=10).until(element_present)

            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'collapsible__toggle'))
            WebDriverWait(self.browser, timeout=10).until(element_present)
        
            self.browser.find_element(By.CLASS_NAME, 'collapsible__toggle').click()
        except Exception as e:
            print(e, -1)
        # получаем HTML-код страницы
        html = self.browser.page_source

        # создаем объект BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # находим нужные элементы и получаем их содержимое
            name = soup.select_one('.product-page__header').text.strip()
        except Exception as e:
            print(e, 1)

        try:
            rating = soup.select_one('.product-review__rating').text.strip()
            # rating_el = soup.find(class_=lambda x: x and x.startswith('star'))
            # rating = ''
            # for class_name in rating_el['class']:
            #     rating_candidate = re.sub('[^1-5]', '', class_name)
            #     if (rating_candidate):
            #         rating = int(rating_candidate)
        except Exception as e:
            print(e, 2)
        
        try:
            review_count = soup.select_one('.product-review__count-review').text.strip()
            review_count = int(re.sub('[^0-9]', '', review_count))
        except Exception as e:
            print(e, 3)

        try:
            article = soup.select_one('.product-article').text.strip().split('\n')[-1]
            article = int(re.sub('[^0-9]', '', article))
        except Exception as e:
            print(e, 4)
        
        try:
            order_count = soup.select_one('.product-order-quantity').text.strip()
            order_count = int(re.sub('[^0-9]', '', order_count))
        except Exception as e:
            print(e, 5)
            
        try:
            price = soup.select_one('.price-block__final-price').text.strip()
            price = int(re.sub('[^0-9]', '', price))
        except Exception as e:
            print(e, 6)

        try:
            discount_element = soup.select_one('.price-block__old-price')
            if discount_element:
                discount = discount_element.text.strip()
                discount = int(re.sub('[^0-9]', '', discount))
            else:
                discount = price
        except Exception as e:
            print(e, 7)
        
        try:
            detail = soup.select_one('.details-section').text
        except Exception as e:
            print(e, 8)
        
        try:
            product_id = int(re.sub('[^0-9]', '', url))
        except Exception as e:
            print(e, 9)

        def volHostV2(e):
            if 0 <= e <= 143:
                return 'https://basket-01.wb.ru/'
            elif 144 <= e <= 287:
                return 'https://basket-02.wb.ru/'
            elif 288 <= e <= 431:
                return 'https://basket-03.wb.ru/'
            elif 432 <= e <= 719:
                return 'https://basket-04.wb.ru/'
            elif 720 <= e <= 1007:
                return 'https://basket-05.wb.ru/'
            elif 1008 <= e <= 1061:
                return 'https://basket-06.wb.ru/'
            elif 1062 <= e <= 1115:
                return 'https://basket-07.wb.ru/'
            elif 1116 <= e <= 1169:
                return 'https://basket-08.wb.ru/'
            elif 1170 <= e <= 1313:
                return 'https://basket-09.wb.ru/'
            elif 1314 <= e <= 1601:
                return 'https://basket-10.wb.ru/'
            elif 1602 <= e <= 1655:
                return 'https://basket-11.wb.ru/'
            else:
                return 'https://basket-12.wb.ru/'

        def constructHostV2(e, t="nm"):
            n = int(e)
            r = n // 100000
            o = n // 1000
            if t == "nm":
                host_url = volHostV2(r)
            else:
                host_url = volFeedbackHost(r)
            return f"{host_url}vol{r}/part{o}/{n}/info"

        def get_price_history():
            request_url = constructHostV2(product_id) + "/price-history.json"
            response = requests.get(request_url)
            return response.json()

        def get_seller():
            request_url = constructHostV2(product_id) + "/sellers.json"
            response = requests.get(request_url)
            return response.json()
        
        try:
            price_history = get_price_history()
            seller = get_seller()
        except Exception as e:
            print(e, 10)

        # try:
        #     # Находим все изображения внутри контейнера со слайдером
        #     product_images = soup.select_one('.product-page__slider').find_all('img')
        # except Exception as e:
        #     print(e, 11)

        # Получаем адреса всех изображений
        # product_image_urls = ['https:' + img['src'] for img in product_images]
        # reviews = self.parse_reviews(id)
        try:
            # Находим все таблицы с классом product-params__table
            tables = soup.find_all('table', {"class": 'product-params__table'})

            # Создаем массив объектов в формате {label, value}
            params = []
            for table in tables:
                for row in table.find_all('tr'):
                    label = row.find('th').text.strip()
                    value = row.find('td').text.strip()
                    params.append({'label': label, 'value': value})
        except Exception as e:
            print(e, 11)

        return {
            'name': name,
            'rating': rating,
            'review_count': review_count,
            'article': article,
            'order_count': order_count,
            'price': price,
            'discount': discount,
            'detail': detail,
            'seller': seller,
            'price_history': price_history,
            'addtional_params': params
            # 'images': product_image_urls
        }

    def parse_reviews(self, product_id):
        url = "https://www.wildberries.ru/catalog/" + str(product_id) + "/feedbacks"
        self.browser.get(url)
        time.sleep(100)
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'product-line__name'))
        WebDriverWait(self.browser, timeout=20).until(element_present)

        # получаем HTML-код страницы
        html = self.browser.page_source

        # создаем объект BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # находим все элементы отзывов
        reviews = soup.select('.feedback')
        print(reviews)

        result = []
        
        # проходимся по каждому отзыву и получаем нужные данные
        for review in reviews:
            name = review.select_one('.feedback__header').text.strip()
            date = review.select_one('.feedback__date')['content']
            rating_el =card.find(class_=lambda x: x and x.startswith('star'))
            rating = ''
            for class_name in rating_el['class']:
                rating_candidate = re.sub('[^1-5]', '', class_name)
                if (rating_candidate):
                    rating = int(rating_candidate)
            content = review.select_one('.feedback__text').text.strip()
            result.append({
                'name': name,
                'date': date,
                'rating': rating,
                'content': content
            })
        while True: continue
        print(result)
        return {}

    def save_to_file(self, content, filepath):
        """
        Сохраняет текст в файл JSON по заданному пути.

        :param content: content, который нужно сохранить в файл
        :type content: str
        :param filepath: путь к файлу, в который нужно сохранить текст
        :type filepath: str
        """
        # Получаем директорию из пути и создаем ее, если ее нет
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Сохраняем текст в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

class ParserConductor(Parser):
    def __init__(self, browser, db_connection):
        super().__init__(browser)
        self.db_connection = db_connection
    
    def parse_category_products_list(self, category):
        # Парсим карточки продуктов на странице списска продуктов категории category
        category_abs_url = "https://www.wildberries.ru" + category['url']
        category_name = category['name']
        # try:
        products_object = self.parse_products_list(category_abs_url, './results/products_list/' + category_name.replace('/', '-') + '.json')
        for product_link in products_object['products']:
            product = products_object['products'][product_link]
            product['category_id'] = category['_id']
            product['wb_id'] = int(re.sub('[^0-9]', '', product_link))

            self.db_connection['products'].replace_one({
                "wb_id": product['wb_id']
            }, product, upsert=True)

        category_id = category['_id']
        parsed_counter = category.get('parsed_counter', 0) + 1  # increment the parsed_counter field

        result = self.db_connection['categories'].update_one(
            {'_id': category_id},
            {'$set': {'parsed_counter': parsed_counter}}
        )

        success_mgs = f'Success parsing category "{category_name}"'
        logger.info(success_mgs)
        # except Exception as e:
        #     error_msg = f'Error parsing category "{category_name}", url: "{category_abs_url}": {str(e)}'
        #     logger.error(error_msg)


    def parse_category_by_id_products_list(self, id):
        category = self.db_connection['categories'].find_one({
            "_id": ObjectId(id)
        })
        if (not category): return print("Такой категории нет", id)
        self.parse_category_products_list(category)

    def parse_categories_products_list(self):
        # Получаем текущую дату
        now = datetime.datetime.now()

        # Генерируем название файла в формате "YYYY-MM-DD-HH-MM.logs"
        filename = now.strftime("%Y-%m-%d-%H-%M-%S") + ".log"

        # Создаем путь к файлу
        path = os.path.join(".", "logs", "products_list", filename)
        logger.add(path, format="{time} {level} {message}", level="INFO")


        # Проверяем, что путь к файлу существует
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        
        get_has_no_childs_category_query = {"$or": [{"has_childs": {"$exists": False}}, {"has_childs": False}]}

        categories = self.db_connection['categories'].find(get_has_no_childs_category_query)
        for category_index, category in enumerate(categories):
            parse_category_products_list(category)
    
    def parse_products_by_files(self, callback):
        # Получаем текущую дату
        now = datetime.datetime.now()

        # Генерируем название файла в формате "YYYY-MM-DD-HH-MM.logs"
        filename = now.strftime("%Y-%m-%d-%H-%M-%S") + ".log"

        path = os.path.join(".", "logs", "products", filename)
        logger.add(path, format="{time} {level} {message}", level="INFO")

        dir_path = './results/products_list/'
        for category_index, filename in enumerate(os.listdir(dir_path)):
            if filename.endswith('.json'):  # проверяем, что файл имеет расширение .json
                filepath = os.path.join(dir_path, filename)
                with open(filepath, 'r') as file:
                    content = json.load(file)
                    category_name = content['meta']['category_name']
                    products = content['products']
                    for product_index, link in enumerate(products):
                        abs_link = 'https://www.wildberries.ru' + link
                        product = content['products'][link]
                        product_name = product['name']
                        try:
                            product = self.parse_product_page(abs_link)
                            product['category_name'] = category_name
                            callback(product)
                            success_mgs = f'Success parsing product "{product_name}" in category "{category_name}", progress: "{int(product_index)}" of {len(products)}'
                            logger.info(success_mgs)
                        except Exception as e:
                            error_msg = f'Error parsing product "{product_name}", "{abs_link}" in category "{category_name}": {str(e)}'
                            logger.error(error_msg)
    
    def re_parse_products(self, category_id = False):
        # Получаем текущую дату
        now = datetime.datetime.now()

        # Генерируем название файла в формате "YYYY-MM-DD-HH-MM.logs"
        filename = now.strftime("%Y-%m-%d-%H-%M-%S") + ".log"

        path = os.path.join(".", "logs", "products-deep-parse", filename)
        logger.add(path, format="{time} {level} {message}", level="INFO")

        query = {}
        if category_id:
            query['category_id'] = ObjectId(category_id)
        print(query)
        products = self.db_connection['products'].find(query)
        
        for product in products:
            product_link = "https://www.wildberries.ru/catalog/"+ str(product['wb_id']) +"/detail.aspx"
            product_name = product['name']
            try:
                parsed_product = self.parse_product_page(product_link)
                product.update(parsed_product)
                seller = parsed_product['seller'].copy()
                seller_from_db = self.db_connection['sellers'].find_one({'nmId': seller['nmId']})
                if seller_from_db:
                    product['seller_id'] = seller_from_db['_id']
                else:
                    seller = self.db_connection['sellers'].insert_one(seller)
                    product['seller_id'] = seller.inserted_id
                product.pop('seller')

                if "parsed_counter" in product:
                    product["parsed_counter"] += 1
                else:
                    product["parsed_counter"] = 1
                self.db_connection['products'].update_one({'_id': product['_id']}, {'$set': product})

                success_mgs = f'Success parsing product "{product_name}", "{product_link}"'
                logger.info(success_mgs)
            except Exception as e:
                error_msg = f'Error parsing product "{product_name}", "{product_link}": {str(e)}'
                logger.error(error_msg)
                continue
            
            
    
    def parse_categories_to_db(self):
        categories = self.parse_categories()
        def recursion_push_categories_to_db(category):
            category_copy = category.copy()
            
            if "childs" in category_copy:
                category_copy.pop('childs')
                category_copy['has_childs'] = True

            category_copy['wb_id'] = category_copy['id']
            category_copy.pop('id')
            pushed_category = self.db_connection['categories'].replace_one({
                "wb_id": category_copy['wb_id']
            }, category_copy, upsert=True)
            pushed_category_id = pushed_category.upserted_id

            if "childs" in category:
                for child_category in category['childs']:
                    child_category['parent'] = pushed_category_id
                    recursion_push_categories_to_db(child_category)
        
        # recursion_push_categories_to_db(categories[0])
        for category in categories:
            recursion_push_categories_to_db(category)