import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import os


def get_metrics(url):
    geckodriver_path = os.path.join(os.getcwd(), 'geckodriver.exe')
    service = Service(geckodriver_path)
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)

    def extract_count(metric_name: str) -> str:
        data = soup.find(string=re.compile(metric_name))
        if data:
            parent = data.find_parent().find_parent().find_parent()
            count_span = parent.find('div').find('span').find('span').find('span')
            return count_span.text if count_span else 'Not found'
        return 'Not found'

    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[1]/div/div/article/div/div/div[3]/div[5]/div[2]/a"))
        )

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        repost_count = extract_count("Reposts")
        print(f"Reposts: {repost_count}")

        quote_count = extract_count("Zitate")
        print(f"Quotes: {quote_count}")

        like_count = extract_count("Gefällt mir")
        print(f"Likes: {like_count}")

        bookmarks_count = extract_count("Lesezeichen")
        print(f"Bookmarks: {bookmarks_count}")

        views_count = extract_count("Mal angezeigt")
        print(f"Views: {views_count}")

    finally:
        driver.quit()

get_metrics("https://x.com/BarackObama/status/1853617803829375120")
