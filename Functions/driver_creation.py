from concurrent.futures import ThreadPoolExecutor
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from Functions.Helpers.common_scrape_functions import scroll
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_drivers(amount: int, headless: bool) -> list[WebDriver]:
    drivers = []
    for i in range(amount):
        drivers.append(create_driver(headless))
    return drivers

def create_driver(headless: bool) -> WebDriver:
    service = Service()
    options = Options()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)
    driver.set_page_load_timeout(10)
    driver.maximize_window()
    return driver

def login_all_drivers(drivers):
    def login(driver: webdriver, username, password):
        driver.get("https://x.com/home")

        time.sleep(1)
        scroll(driver, 500)

        # Locate and interact with email/username field
        email_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[text()='Telefonnummer, E-Mail-Adresse oder Nutzername']"))
        )
        email_field = email_text.find_element(By.XPATH, "ancestor::*[4]")
        time.sleep(1)
        email_field.click()
        driver.switch_to.active_element.send_keys(username)

        # Click "Weiter" to proceed
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Weiter']/ancestor::*[2]"))
        )
        next_button.click()

        # Handle unusual activity prompt if it appears
        try:
            unusual_activity = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'ungewöhnliche Anmeldeaktivität')]"))
            )
            driver.switch_to.active_element.send_keys(username)
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Weiter']/ancestor::*[2]"))
            )
            next_button.click()
        except:
            pass

        time.sleep(1)

        driver.switch_to.active_element.send_keys(password)

        time.sleep(1)
        final_login_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "(//span[text()='Anmelden'])/ancestor::*[3]"))
        )
        final_login_button.click()
        time.sleep(3)

    def get_login_data():
        def read_login_data():
            login_data = {}
            with open('../login_data', 'r') as file:
                for line in file:
                    key, value = line.strip().split('=')
                    login_data[key] = value
            return login_data

        unfiltered_data = read_login_data()

        login_data = []
        i = 1
        while True:
            username_key = f'username{i}'
            password_key = f'password{i}'
            if username_key in unfiltered_data and password_key in unfiltered_data:
                login_data.append({
                    'username': unfiltered_data[username_key],
                    'password': unfiltered_data[password_key]
                })
                i += 1
            else:
                break

        if not login_data:
            raise ValueError("No valid login data found in the login_data.txt file.")

        for data in login_data:
            if not data['username'] or not data['password']:
                raise ValueError(f"Username or password is missing for a login entry.")

        return login_data

    logins = get_login_data()

    if len(logins) < len(drivers):
        raise ValueError(
            f"Insufficient login data: {len(logins)} logins provided, but {len(drivers)} drivers require logins.")

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(login, driver, logins[i]['username'], logins[i]['password'])
            for i, driver in enumerate(drivers)
        ]
        for future in futures:
            future.result()

def quit_all_drivers(drivers: list[WebDriver]):
    for driver in drivers:
        driver.quit()
