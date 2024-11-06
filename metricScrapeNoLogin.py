from commonMethods import extract_count
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import os
import csv
from datetime import datetime


def get_metrics_nologin(url):
    geckodriver_path = os.path.join(os.getcwd(), 'geckodriver.exe')
    service = Service(geckodriver_path)
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)

    try:
        driver.get(url)

        WebDriverWait(driver, 10).until( #some path which cheks if side is loaded
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[1]/div/div/article/div/div/div[3]/div[5]/div/div/div[1]/button/div/div[2]/span/span/span"))
        )

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        repost_count = extract_count(soup, "Reposts")
        quote_count = extract_count(soup, "Zitate")
        like_count = extract_count(soup, "Gefällt mir")
        bookmarks_count = extract_count(soup, "Lesezeichen")
        views_count = extract_count(soup, "Mal angezeigt")

        return repost_count, quote_count, like_count, bookmarks_count, views_count
    finally:
        driver.quit()