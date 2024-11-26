from selenium.common import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from commonMethods import *


def login(driver):
    try:
        driver.get("https://x.com/home")

        time.sleep(1)
        scroll(driver, 500)

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
            unusual_activity = WebDriverWait(driver, 10).until(
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

def get_metrics_login(url, driver, seen_urls, og_post_needed): #login before using this function needed
    time.sleep(1)
    driver.get(url)
    time.sleep(1)
    print("Scraping: " + str(url))
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Hmm...this page doesn’t exist. Try searching for something else.]")))
        return None, None, seen_urls
    except Exception:
        pass

    og_tweet = None

    if og_post_needed:
        pattern = re.compile(r"replies|reposts|likes|bookmarks|views")
        og_post_data = get_main_metrics(driver, pattern)

        if not og_post_data:
            print("FAILED TO GET DATA + " + url)
            return None, None, seen_urls

        reply_count, repost_count, like_count, bookmark_count, view_count = get_metrics(og_post_data)
        og_tweet = Tweet(reply_count, repost_count, like_count, bookmark_count, view_count, "", url)

    if og_post_needed:
        sorting_successfull = click_sort_by_likes_button(driver) #makes twitter replies sorted by likes,
        if not sorting_successfull:
            print("FAILED TO SORT REPLIES!!!")
            return None, None, seen_urls

    seen_urls.add(url)
    replies, seen_urls = get_all_replies(driver, url, seen_urls, og_post_needed)

    return og_tweet, replies, seen_urls

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

def get_all_replies(driver, replies_to_url, seen_urls, replies_sorted) -> tuple:
    def is_valid_reply(current_element):
        sibling = current_element.find_previous_sibling()
        if sibling:
            first_child = sibling.contents[0] if sibling.contents else None
            if first_child and hasattr(first_child, 'children'):
                return not bool(list(first_child.children))
        return True

    def is_spam_button(current_element):
        try:
            element = current_element.find().find().find()
            if element and element.name == "button":
                return "Show probable spam" in element.text
            else:
                return False
        except:
            return False


    unique_replies = []

    cycles_since_new_found = 0
    while cycles_since_new_found < 5:
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        posts_parent = soup.find(attrs={"aria-label": "Timeline: Conversation"}).find()

        new_unique_replies_found = []

        for current_element in posts_parent.find_all(recursive=False):
            try:
                if is_spam_button(current_element):
                    print("spam button reached, ending")
                    unique_replies.extend(new_unique_replies_found)
                    print("found replies: " + str(len(unique_replies)))
                    return unique_replies, seen_urls
                if not is_valid_reply(current_element):
                    continue

                #path from post to its metrics
                metrics_element = current_element.find('div').find('div').find('article').find('div').find('div').contents[-1].contents[-1].contents[-1].find().find()

                #path from metrics_element to href with url
                href_element = metrics_element.contents[3].find()
                url = "https://x.com" + '/'.join(href_element.get('href').split("/")[:-1])

                if url not in seen_urls:
                    cycles_since_new_found = 0
                    seen_urls.add(url)
                    data = metrics_element.get("aria-label")
                    reply_count, repost_count, like_count, bookmark_count, view_count = get_metrics(data)

                    if not (reply_count == 0 and repost_count == 0):
                        new_unique_replies_found.append(Tweet(reply_count, repost_count, like_count, bookmark_count, view_count, replies_to_url, url))

                    if replies_sorted and like_count < 3 and reply_count == 0 and repost_count == 0:
                        print("reached posts with no interaction, ending")
                        unique_replies.extend(new_unique_replies_found)
                        print("found replies: " + str(len(unique_replies)))
                        return unique_replies, seen_urls
            except Exception as e:
                pass

        if new_unique_replies_found:
            unique_replies.extend(new_unique_replies_found)
            print("current replies: " + str(len(unique_replies)))
        else:
            cycles_since_new_found += 1
            print("no new found, scrolling")
            scroll(driver, 2000)
            time.sleep(1)
    print("no new found in 5 cycles. Ending")
    print("found replies: " + str(len(unique_replies)))
    return unique_replies, seen_urls

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

def click_sort_by_likes_button(driver):
    def scroll_until_appears():
        tries = 10

        while tries > 0:
            try:
                button = driver.find_element(By.XPATH, '//button[@aria-label="Reply"]')
                sort_button = button.find_element(By.XPATH, './following-sibling::*[1]')
                return sort_button
            except:
                scroll(driver, 400)
                tries -= 1
                time.sleep(1)
    tries = 3
    while tries > 0:
        try:
            sort_button = scroll_until_appears()
            sort_button.click()

            likes_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Likes']"))
            )
            likes_button.click()
            time.sleep(1)
            return True
        except Exception:
            tries -= 1
            driver.refresh()
            print("Sort failed, refreshing and waiting a minute")
            time.sleep(60)


def scroll(driver, y_range):
    driver.execute_script(f"window.scrollBy(0,{y_range})", "")

