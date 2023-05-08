from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType

import atexit

def get_browser(headless=False) -> webdriver:
    """Return a Selenium browser."""
    options = webdriver.ChromeOptions()
    # useragent = UserAgent()
    # options.add_argument(f'user-agent={useragent.random}')
    if headless:
        options.add_argument('--headless')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    # options.add_argument(f'--proxy-server=http://103.155.54.26:83')

    # Создаем объект WebDriver с настройками
    browser = webdriver.Remote(
        command_executor='http://185.166.196.222:4444/wd/hub',
        # desired_capabilities=webdriver.DesiredCapabilities.CHROME,
        options=options
    )

    def close_browser():
        browser.quit()

    atexit.register(close_browser)

    return browser