import re
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
from commonMethods import extract_post_id, twitter_time_to_python_time, Tweet


def login(driver):
    try:
        driver.get("https://x.com/home")

        time.sleep(1)
        scroll_to_bottom(driver)

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

        time.sleep(1)
        # Enter password and complete login
        #WebDriverWait(driver, 300).until(
        #    EC.presence_of_element_located((By.XPATH, "//span[text()='Passwort']"))
        #)
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
    time.sleep(1)
    driver.get(url)

    time.sleep(1)

    pattern = re.compile(r"replies|reposts|likes|bookmarks|views")

    og_post_data = get_main_metrics(driver, pattern)

    if not og_post_data:
        print("No data element found")
        return 0, 0, 0, 0, 0

    reply_count, repost_count, like_count, bookmark_count, view_count = get_metrics(og_post_data)
    time_of_post = ""
    post_id = extract_post_id(url)

    og_tweet = Tweet(reply_count, repost_count, like_count, bookmark_count, view_count, "",
                         time.time() - twitter_time_to_python_time(time_of_post) / 60, url)

    expected = reply_count

    replies = []
    #region replies
    if get_replies:
        replies_raw = get_all_replies(driver, int(reply_count * 0.8))
        for reply_raw in replies_raw:
            data = reply_raw.data
            url = reply_raw.url
            reply_count, repost_count, like_count, bookmark_count, view_count = get_metrics(data)
            replies.append(Tweet(reply_count, repost_count, like_count, bookmark_count, view_count, post_id, "0", url))
    #endregion
    print("replies: " + str(len(replies)) + " / " + str(expected))
    return og_tweet, replies

def get_metrics(data_text: str) -> tuple: #expects data.get('aria label'....)
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

def get_all_replies(driver, replies_expected): #issue here
    def is_valid_reply(current_element):
        try:
            sibling = current_element.find_element(By.XPATH, "following-sibling::*")
            return bool(sibling.find_elements(By.XPATH, "./*"))
        except NoSuchElementException:
            return True

    class Reply:
        def __init__(self, url, data):
            self.url = url
            self.data = data

        def __hash__(self):
            return hash((self.url, self.data))

        def __eq__(self, other):
            return (self.url, self.data) == (other.url, other.data)

    posts_path = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div"
    metrics_path = "./div[3]/div/div/article/div/div/div[2]/div[2]/div[3]/div/div"

    unique_replies = set()
    seen_urls = set()

    while True: #shall continue until no more children load
        #get all elements in the posts_path
        #if first loop, remove the first post as it is the original
        #go trough all elements
        #check if element is a valid post
        #extract the data and the url
        #if no more elements, scroll down
        #if still no more elements, exit



        all_elements = driver.find_element(By.XPATH, posts_path + './*')
        for current_element in all_elements:
            try:
                if not is_valid_reply(current_element):
                    continue

                metrics_element = current_element.find_element(By.XPATH, metrics_path)

                href_element = metrics_element.find_element(By.XPATH, ".//a[@href]")
                url = href_element.get_attribute("href")
                data = metrics_element.get_attribute("aria-label")

                if url and url not in seen_urls:
                    unique_replies.add(Reply(url, data))
                    seen_urls.add(url)
                    print(f"Found reply: {url}")

                while True:
                    try:
                        driver.find_element(By.XPATH, next_element_path)
                        break
                    except NoSuchElementException:
                        driver.execute_script("window.scrollBy(0,500)")
                        time.sleep(0.5)

                print(f"Found {len(unique_replies)} / {replies_expected}")
            except Exception as e:
                print("failed: " + str(e))

    return list(unique_replies)


def get_main_metrics(driver, pattern) -> str: #scrolls until it finds the first pattern. Needed for posts with big images
    attempts = 0
    max_attempts = 20

    while attempts < max_attempts:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        og_post_data = soup.find(attrs={"aria-label": pattern})

        if og_post_data:
            return og_post_data.get("aria-label")

        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(0.5)
        attempts += 1

    return None


def scroll_to_bottom(driver):
    driver.execute_script("window.scrollBy(0,500)", "")

