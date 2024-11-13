import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from commonMethods import extract_post_id, twitter_time_to_python_time, Tweet


def login(driver):
    try:
        driver.get("https://x.com/home")
        time.sleep(5)  # manually close firefox windows
        # Wait for the page to load and locate the login button
        login_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Anmelden']"))
        )
        time.sleep(1)
        login_button.click()

        # Locate and interact with email/username field
        email_text = WebDriverWait(driver, 300).until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[text()='Telefonnummer, E-Mail-Adresse oder Nutzername']"))
        )
        email_field = email_text.find_element(By.XPATH, "ancestor::*[4]")
        time.sleep(1)
        email_field.click()
        driver.switch_to.active_element.send_keys("shapovalov@connected-organization.de")

        # Click "Weiter" to proceed
        next_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Weiter']/ancestor::*[2]"))
        )
        next_button.click()

        # Handle unusual activity prompt if it appears
        try:
            unusual_activity = WebDriverWait(driver, 300).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'ungewöhnliche Anmeldeaktivität')]"))
            )
            driver.switch_to.active_element.send_keys("OlegShap05")
            next_button = WebDriverWait(driver, 300).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Weiter']/ancestor::*[2]"))
            )
            next_button.click()
        except:
            print("No unusual activity prompt detected")

        # Enter password and complete login
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='Passwort']"))
        )
        driver.switch_to.active_element.send_keys("Twitter48311!")

        time.sleep(1)
        final_login_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.XPATH, "(//span[text()='Anmelden'])/ancestor::*[3]"))
        )
        final_login_button.click()
        time.sleep(3)
        return True
    except Exception as e:
        print("Login failed:", e)
        return False

def get_metrics_login(url, driver, get_replies): #login before using this function needed
    driver.get(url)

    #scroll_to_bottom(driver)

    time.sleep(5)

    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    data = soup.findAll(attrs={"aria-label": re.compile(r"replies|reposts|likes|bookmarks|views")})
    time_stamps = soup.find_all('time', datetime=True) #time only works as long as their only occurences are on the posts

    if len(data) != len(time_stamps):
        print("data and time not synchrone!!!")

    if data is None:
        print("No data element found")
        return 0, 0, 0, 0, 0

    post_data = data[0]
    reply_count, repost_count, like_count, bookmark_count, view_count = get_metrics(post_data)
    time_of_post = time_stamps[0].text
    post_id = extract_post_id(url)

    og_tweet = Tweet(reply_count, repost_count, like_count, bookmark_count, view_count, "",
                         time.time() - twitter_time_to_python_time(time_of_post) / 60)

    replies = []
    #region replies
    if get_replies:
        replies_data = data[1:]
        time_stamps_data = time_stamps[1:]
        for reply_data in replies_data:
            time_text = "0"
            reply_count, repost_count, like_count, bookmark_count, view_count = get_metrics(reply_data)
            replies.append(Tweet(reply_count, repost_count, like_count, bookmark_count, view_count, post_id, "0"))
    #endregion
    print("replies found " + str(len(replies)))
    return og_tweet, replies

def get_metrics(data):
    data_text = data.get("aria-label")
    replies_match = re.search(r"(\d+)\s+replies", data_text)
    reposts_match = re.search(r"(\d+)\s+reposts", data_text)
    likes_match = re.search(r"(\d+)\s+likes", data_text)
    bookmarks_match = re.search(r"(\d+)\s+bookmarks", data_text)
    views_match = re.search(r"(\d+)\s+views", data_text)

    reply_count = repost_count = like_count = bookmark_count = view_count = 0

    if replies_match:
        reply_count = int(replies_match.group(1))
    if reposts_match:
        repost_count = int(reposts_match.group(1))
    if likes_match:
        like_count = int(likes_match.group(1))
    if bookmarks_match:
        bookmark_count = int(bookmarks_match.group(1))
    if views_match:
        view_count = int(views_match.group(1))
    return reply_count, repost_count, like_count, bookmark_count, view_count


def scroll_to_bottom(driver, scroll_pause_time=2):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height