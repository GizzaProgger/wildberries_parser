from browser_factory import get_browser
from Parser import Parser

browser = get_browser()

parser = Parser(browser)
parser.parse_categories()