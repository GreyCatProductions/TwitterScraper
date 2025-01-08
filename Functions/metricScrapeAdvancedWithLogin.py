import logging
import traceback
import time

from bs4 import NavigableString
from selenium.common import TimeoutException
from selenium.webdriver.firefox.webdriver import WebDriver

from Functions.Helpers.common_scrape_functions import *
from Functions.Helpers.saver import *
from Functions.Helpers.extractor import *
from datetime import datetime
import shutil
from Objects.Tweet import Tweet


def get_tweets(url, driver, sorting_needed, quote_to, seen_urls, hour_final_path): #login before using this function needed
    time.sleep(1)
    driver.get(url)
    time.sleep(1)
    print("Scraping: " + str(url))

    if not check_if_page_exists(driver):
        return None, None, seen_urls
    retries = 5
    request_block = True
    while retries > 0 and request_block:
        try:
            WebDriverWait(driver, 2 ).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Something went wrong. Try reloading.']")))
            print("Cant load. Requests probably blocked. Retrying in 30 seconds")
            time.sleep(30)
            driver.refresh()
            retries -= 1
        except Exception:
            request_block = False

    screenshot_save_path = make_and_save_screenshot(driver, hour_final_path)

    if sorting_needed:
        sorting_successfull = click_sort_by_likes_button(driver) #makes twitter replies sorted by likes,
        if not sorting_successfull:
            print("FAILED TO SORT REPLIES!!!")
            return None, None, seen_urls

    tweet, unique_replies, seen_urls = get_all_posts(driver, url, sorting_needed, quote_to, seen_urls)

    post_id = extract_post_id(tweet.url)
    new_file_name = f"{post_id}.png"
    new_file_path = os.path.join(os.path.dirname(screenshot_save_path), new_file_name)
    shutil.move(screenshot_save_path, new_file_path)

    return tweet, unique_replies, seen_urls

def get_all_posts(driver: WebDriver, replies_to_url: str, replies_sorted: bool, quote_to: str, seen_urls: set[str]) -> (Tweet, list[Tweet], set[str]):
    time.sleep(1)
    unique_replies: [Tweet] = []
    og_tweet: Tweet = None

    cycles_since_new_found = 0
    while cycles_since_new_found < 30:
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        try:
            wait_until_loaded(driver, '//*[@aria-label="Home timeline"]', 10)
        except TimeoutException:
            print("Failed to load home timeline")
            driver.refresh()
            time.sleep(60)
            continue

        posts_parent = soup.find(attrs={"aria-label": "Timeline: Conversation"}).find()

        for current_element in posts_parent.find_all(recursive=False):
            try:
                if og_tweet is not None:
                    if is_ad(soup, current_element): #nicht ganz klar hier
                        print("ad found, skipping")
                        continue

                    if is_spam_button(current_element):
                        print("spam button reached, ending")
                        print("found replies: " + str(len(unique_replies)))
                        return og_tweet, unique_replies, seen_urls

                    if is_additional_replies_button(current_element):
                        print("additional replies button reached, ending")
                        print("found replies: " + str(len(unique_replies)))
                        return og_tweet, unique_replies, seen_urls

                    if not is_valid_reply(current_element):
                        continue

                try:
                    metrics_element, href_element = get_metrics_and_href_element(current_element)
                    href = href_element.get("href")
                    url = "https://x.com" + normalize_href(href)
                    user_url = extract_post_poster(url)
                    data = metrics_element.get("aria-label")
                    reply_count, repost_count, like_count, bookmark_count, view_count = extract_metrics(data)
                    time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                except Exception as e:
                    print("skipped, failed")
                    print(e)
                    continue

                #skip until tweet is found
                if og_tweet is None:
                    if extract_post_id(url) == extract_post_id(replies_to_url):
                        print("Found main tweet " + url)
                        og_tweet = Tweet(reply_count, repost_count, like_count, bookmark_count, view_count, "", url, time_stamp, quote_to, user_url)
                        seen_urls.add(og_tweet.url)

                    continue

                if url not in seen_urls:
                    cycles_since_new_found = 0
                    #process unique reply
                    if reply_count > 3:
                        print("Found reply " + url)
                        unique_replies.append(Tweet(reply_count, repost_count, like_count, bookmark_count, view_count, replies_to_url, url, time_stamp, "", user_url))
                        print("current replies: " + str(len(unique_replies)))
                        seen_urls.add(url)

                    if replies_sorted and like_count < 3 and reply_count == 0 and repost_count == 0:
                        print("reached posts with no interaction, ending")
                        print("found replies: " + str(len(unique_replies)))
                        return og_tweet, unique_replies, seen_urls
            except Exception as e:
                logging.error(f"failed to process reply\n"
                              f"{e}"
                              f"{traceback.format_exc()}")
                continue


        cycles_since_new_found += 1
        print("no new found, scrolling")
        if not scroll(driver, 1500):
            print("scrolling further impossible, ending")
            return og_tweet, unique_replies, seen_urls
        time.sleep(1)

    print("no new found in 30 cycles. Ending")
    print("found replies: " + str(len(unique_replies)))
    return og_tweet, unique_replies, seen_urls

def is_valid_reply(current_element: NavigableString) -> bool:
    sibling = current_element.find_previous_sibling()
    if sibling:
        first_child = sibling.contents[0] if sibling.contents else None
        if first_child and hasattr(first_child, 'children'):
            return not any(list(first_child.children))
    return True

def is_spam_button(current_element: NavigableString) -> bool:
    try:
        element = current_element.find().find().find()
        if element and element.name == "button":
            return "Show probable spam" in element.text
        else:
            return False
    except Exception as e:
        return False

def is_additional_replies_button(current_element):
    try:
        text_element = current_element.find().find().find().find().find().contents[1].find().find().find().find().find()
        if "Show additional replies, including those that may contain offensive content" in text_element.text and text_element.name == "span":
            return True
        return False
    except:
        return False

def is_ad(soup: BeautifulSoup, current_element):
    if current_element.find(string="Ad") and soup.find(attrs={"data-testid": "placementTracking"}):
        return True

    return False

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
    return False
