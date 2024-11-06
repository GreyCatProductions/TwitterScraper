import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import os
import time

def get_metrics(url):
    geckodriver_path = os.path.join(os.getcwd(), 'geckodriver.exe')
    service = Service(geckodriver_path)
    options = Options()
    #options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)

    def extract_count(metric_name: str) -> str:
        data = soup.find(string=re.compile(metric_name))
        if data:
            parent = data.find_parent().find_parent().find_parent()
            count_span = parent.find('div').find('span').find('span').find('span')
            return count_span.text if count_span else 'Not found'
        return 'Not found'

    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    def login():
        try:
            # Wait for the page to load and locate the login button
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Anmelden']"))
            )
            login_button.click()

            # Locate and interact with email/username field
            email_text = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[text()='Telefonnummer, E-Mail-Adresse oder Nutzername']"))
            )
            email_field = email_text.find_element(By.XPATH, "ancestor::*[4]")
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

            print("Logged in successfully")
            return True
        except Exception as e:
            print("Login failed:", e)
            return False
    try:
        driver.get(url)

        if not login():
            return False

        time.sleep(20)
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
        return
        driver.quit()

get_metrics("https://x.com/BarackObama/status/1853617803829375120")
