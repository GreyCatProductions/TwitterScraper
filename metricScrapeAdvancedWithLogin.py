import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import os

def get_metrics_login(url):
    geckodriver_path = os.path.join(os.getcwd(), 'geckodriver.exe')
    service = Service(geckodriver_path)
    options = Options()
    #options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)

    def login():
        try:
            # Wait for the page to load and locate the login button
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Anmelden']"))
            )
            time.sleep(1)
            login_button.click()

            # Locate and interact with email/username field
            email_text = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[text()='Telefonnummer, E-Mail-Adresse oder Nutzername']"))
            )
            email_field = email_text.find_element(By.XPATH, "ancestor::*[4]")
            time.sleep(1)
            email_field.click()
            driver.switch_to.active_element.send_keys("shapovalov@connected-organization.de")

            # Click "Weiter" to proceed
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Weiter']/ancestor::*[2]"))
            )
            next_button.click()

            # Handle unusual activity prompt if it appears
            try:
                unusual_activity = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//span[contains(text(), 'ungewöhnliche Anmeldeaktivität')]"))
                )
                driver.switch_to.active_element.send_keys("OlegShap05")
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Weiter']/ancestor::*[2]"))
                )
                next_button.click()
            except:
                print("No unusual activity prompt detected")

            # Enter password and complete login
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Passwort']"))
            )
            driver.switch_to.active_element.send_keys("Twitter48311!")
            final_login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "(//span[text()='Anmelden'])[2]/ancestor::*[3]"))
            )
            final_login_button.click()
            return True
        except Exception as e:
            print("Login failed:", e)
            return False
    try:
        driver.get(url)

        if not login():
            return False

        WebDriverWait(driver, 10).until( #some path that checks if side is loaded
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[1]/div/div/article/div/div/div[3]/div[5]/div/div/div[1]/button/div/div[2]/span/span/span"))
        )

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        counts = {
            "replies": 0,
            "reposts": 0,
            "likes": 0,
            "bookmarks": 0,
            "views": 0
        }

        data = soup.find(attrs={"aria-label": re.compile(r"replies|reposts|likes|bookmarks|views")})

        if data:
            data_text = data.get("aria-label")
            pattern = r"(\d+)\s*(replies|reposts|likes|bookmarks|views)"
            matches = re.findall(pattern, data_text)

            for count, label in matches:
                counts[label] = int(count)

        reply_count = counts["replies"]
        repost_count = counts["reposts"]
        like_count = counts["likes"]
        bookmark_count = counts["bookmarks"]
        view_count = counts["views"]

        return reply_count, repost_count, like_count, bookmark_count, view_count
    finally:
        driver.quit()