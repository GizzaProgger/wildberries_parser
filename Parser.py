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
        self.browser.get("https://www.wildberries.ru/")

        # Находим элемент .nav-element__burger на странице
        burger_icon = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.nav-element__burger')))
    
        # Кликаем на элемент .nav-element__burger
        burger_icon.click()

        WebDriverWait(self.browser, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.j-menu-active')))

        menu_element = WebDriverWait(self.browser, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'a.menu-burger__main-list-link')))
        
        html = self.browser.page_source

        # Используем BeautifulSoup для парсинга HTML-кода
        soup = BeautifulSoup(html, "html.parser")

        # Находим элементы главных категорий
        main_categories = soup.select('a.menu-burger__main-list-link')

        # Создаем пустой словарь для хранения категорий и подкатегорий
        categories = {}


        # Проходимся по каждой главной категории и получаем ее подкатегории
        for i in range(len(main_categories)):
            main_category_element = self.browser.find_elements(By.CSS_SELECTOR, 'a.menu-burger__main-list-link')[i]
            
            # Создаем экземпляр класса ActionChains
            actions = ActionChains(self.browser)

            print("Выполняем наведение мыши на элемент .nav-element__burger")
            actions.move_to_element(main_category_element).perform()

            print("Ждем, пока загрузятся все подкатегории")
            WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.j-menu-drop-link')))

            print("Получаем HTML-код подкатегорий")
            html = self.browser.page_source
            soup = BeautifulSoup(html, "html.parser")

            print("Находим элементы подкатегорий")
            sub_categories = soup.select('a.j-menu-drop-link')

            print("Добавляем главную категорию в словарь")
            categories[main_categories[i].text] = {}

            print("Сохраняем главную категорию")
            main_category_name = main_categories[i].text
            main_category_url = main_categories[i]['href']
            categories[main_category_name] = {"url": main_category_url, "subcategories": {}}

            print("Проходимся по каждой подкатегории и добавляем ее в словарь")
            for sub_category in sub_categories:
                sub_category_name = sub_category.text
                sub_category_url = sub_category['href']
                categories[main_category_name]["subcategories"][sub_category_name] = sub_category_url

            self.save_to_file(json.dumps(categories, ensure_ascii=False), "./results/categories/all.json")
        
        return categories

    def parse_products_list(self, items_list_url, filepath):
        data = {
            'meta': {},
            'products': {}
        }
        # Открыть страницу
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

            rating_el =card.find(class_=lambda x: x and x.startswith('star'))
            rating = ''
            for class_name in rating_el['class']:
                rating_candidate = re.sub('[^1-5]', '', class_name)
                if (rating_candidate):
                    rating = int(rating_candidate)

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
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'product-page__header'))
        WebDriverWait(self.browser, timeout=10).until(element_present)
        
        # получаем HTML-код страницы
        html = self.browser.page_source

        # создаем объект BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # находим нужные элементы и получаем их содержимое
        name = soup.select_one('.product-page__header').text.strip()

        rating_el = soup.find(class_=lambda x: x and x.startswith('star'))
        rating = ''
        for class_name in rating_el['class']:
            rating_candidate = re.sub('[^1-5]', '', class_name)
            if (rating_candidate):
                rating = int(rating_candidate)

        review_count = soup.select_one('.product-review__count-review').text.strip()
        review_count = int(re.sub('[^0-9]', '', review_count))

        article = soup.select_one('.product-article').text.strip().split('\n')[-1]
        article = int(re.sub('[^0-9]', '', article))
        
        order_count = soup.select_one('.product-order-quantity').text.strip()
        order_count = int(re.sub('[^0-9]', '', order_count))
        
        price = soup.select_one('.price-block__final-price').text.strip()
        price = int(re.sub('[^0-9]', '', price))

        old_price = soup.select_one('.price-block__old-price').text.strip()
        old_price = int(re.sub('[^0-9]', '', old_price))

        detail = soup.select_one('.details-section').text

        # получаем индекс символа / перед id
        slash_index = url.rfind('/')

        # извлекаем id из URL
        id = url[slash_index + 1:url.find('/', slash_index + 1)]

        # reviews = self.parse_reviews(id)
        
        return {
            'name': name,
            'rating': rating,
            'review_count': review_count,
            'article': article,
            'order_count': order_count,
            'price': price,
            'old_price': old_price,
            'detail': detail
        }

    def parse_reviews(self, product_id):
        url = "https://www.wildberries.ru/catalog/" + str(product_id) + "/feedbacks"
        self.browser.get(url)

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
    def __init__(self, browser):
        super().__init__(browser)
    
    def parse_categories_products_list(self, categories_filepath):
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

        with open(categories_filepath, 'r') as f:
            categories = json.load(f)
        
        for category_index, category_name in enumerate(categories):
            subcategories = categories[category_name]['subcategories']
            for subcategory_index, sub_categories_name in enumerate(subcategories):
                if sub_categories_name == category_name:
                    continue
                try:
                    subcategory_url = subcategories[sub_categories_name]
                    self.parse_products_list(subcategory_url, './results/products_list/' + sub_categories_name.replace('/', '-') + '.json')
                    success_mgs = f'Success parsing subcategory "{sub_categories_name}" in category "{category_name}", progress: "{int(subcategory_index)}" of {len(subcategories)}'
                    logger.info(success_mgs)
                except Exception as e:
                    error_msg = f'Error parsing subcategory "{sub_categories_name}" in category "{category_name}": {str(e)}'
                    logger.error(error_msg)
                    continue
            logger.info(
                f'Success parsing Category "{category_name}", progress: "{int(category_index)}" of {len(categories)}'
            )
    
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