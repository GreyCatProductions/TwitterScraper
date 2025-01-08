from time import sleep

from metricScrapeNoLogin import *
from metricScrapeAdvancedWithLogin import *
from user_scrape import *
from concurrent.futures import ThreadPoolExecutor
import time
import logging
import queue

#region logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scrape_metrics.log',
    filemode='a'
)
#endregion

def scrape(urls, driver, cycle, detailed_folders):
    def process_tweet_and_replies(
            url: str,
            is_root: bool,
            quote_to: str,
            extendable_path: str,
            depth: int = 0,
            seen_urls: set = set(),
            users: set = set(),
            total_replies_processed: int = 0):

        retries_left = 10 if is_root else 3

        while retries_left > 0:
            try:
                total_replies_found = 0

                tweet, replies, seen_urls = get_tweets(url, driver, is_root, quote_to, seen_urls, hour_final_path)

                if tweet is None:
                    print(f"Failed to scrape tweet: {url}")
                    return 0, 0, users, total_replies_processed

                if replies:
                    try:
                        save_tweets(replies, total_csv_path)
                    except Exception as save_error:
                        print("Error while saving replies!")
                        logging.error(save_error)

                if is_root:
                    total_replies_found += tweet.reply_count
                    users.add(tweet.user_url)

                    file_path_og_post = os.path.join(dir_path, "og_post.csv")
                    save_tweets([tweet], total_csv_path)
                    if detailed_folders:
                        save_tweets([tweet], file_path_og_post)

                replies_with_spread = len(replies)

                for i, reply in enumerate(replies):
                    reply_dir = os.path.join(extendable_path, str(extract_post_id(reply.url)))
                    if detailed_folders:
                        os.makedirs(reply_dir, exist_ok=True)
                        reply_post_path = os.path.join(reply_dir, "reply.csv")
                        save_tweets([reply], reply_post_path)

                    if is_root and i % 5 == 0 and i != 0:
                        elapsed_time = time.time() - start_time
                        avg_time_per_first_layer_reply = elapsed_time / i
                        avg_time_per_reply = elapsed_time / total_replies_processed
                        logging.info(
                            f"--- Progress Report for Root URL: {url} ---\n"
                            f"Total replies: {total_replies_found}\n"
                            f"Replies processed: {total_replies_processed}\n"
                            f"First Layer Replies Processed: {i}/{len(replies)}\n"
                            f"Replies With Spread Found: {replies_with_spread}\n"
                            f"Time Spent: {elapsed_time:.2f} seconds\n"
                            f"Avg Time Per Reply (First Layer): {avg_time_per_first_layer_reply:.2f} seconds\n"
                            f"Avg Time Per Reply (All layers): {avg_time_per_reply:.2f} seconds\n")

                    if reply.reply_count > 0:
                        try:
                            total_replies_processed += 1
                            users.add(reply.user_url)

                            sub_replies, sub_spread, sub_users, sub_processed = process_tweet_and_replies(
                                url=reply.url,
                                is_root=False,
                                quote_to="",
                                extendable_path=reply_dir,
                                depth=depth + 1,
                                seen_urls=seen_urls,
                                users=users,
                                total_replies_processed=total_replies_processed
                            )

                            users.update(sub_users)
                            replies_with_spread += sub_spread
                            total_replies_found += reply.reply_count + sub_replies
                            total_replies_processed = sub_processed
                        except Exception as sub_error:
                            print(f"Failed to process reply: {reply.url}")
                            print(sub_error)
                            continue
                return total_replies_found, replies_with_spread, users, total_replies_processed

            except Exception as main_error:
                print(f"Failed to scrape tweet: {url}")
                print(main_error)
                driver.refresh()
                time.sleep(10)
                retries_left -= 1

        return 0, 0, users, total_replies_processed

    for url in urls:
        try:
            logging.info("-------------------- SCRAPING: " + url + " --------------------")
            start_time = time.time()
            dir_path = os.path.join("data", str(extract_post_id(url)), str(cycle) + "h")
            total_csv_path = os.path.join(dir_path, "total.csv")
            hour_final_path = dir_path
            os.makedirs(dir_path, exist_ok=True)

            def process_replies():
                replies_total, replies_with_spread_total, user_urls, tweets_processed = process_tweet_and_replies(url, True, "", dir_path)
                if replies_total != -1:
                    logging.info(
                        "---------- Reply scrape successfully done for URL: %s (Phase 1 / 4) ----------\n"
                        "time needed: %.2f\n"
                        "total replies (all layers): %d\n"
                        "tweets processed: %d\n"
                        "replies with spread: %d\n"
                        "amount_of unique users: %d",
                        url, time.time() - start_time, replies_total, tweets_processed, replies_with_spread_total, len(user_urls))
                else:
                    logging.info("---------- FAILED to get replies for URL: %s ----------", url)
                    return None

                return user_urls
            user_urls = process_replies()
            replies_failed = user_urls is None

            def process_quotes():
                getting_quotes_start_time = time.time()
                quote_urls_with_spread, total_quotes_count = get_all_quote_urls(driver, url)
                if quote_urls_with_spread != -1:
                    logging.info(
                        "---------- Getting all quotes successfully done for URL: %s (Phase 2 / 4) ----------\n"
                        "total time: %.2f\n"
                        "time needed: %.2f\n"
                        "total quotes found: %d \nq"
                        "quotes with spread found: %d",
                        url, time.time() - start_time, time.time() - getting_quotes_start_time, total_quotes_count,
                        len(quote_urls_with_spread))
                else:
                    logging.info("---------- FAILED to get quotes for URL: %s ----------", url)
                    return

                processing_quotes_start_time = time.time()
                quote_replies_total = quotes_spread_total = quote_tweets_processed_total = 0
                for quote_url in quote_urls_with_spread:
                    quote_replies, quotes_with_spread, quote_users, quote_tweets_processed = process_tweet_and_replies(quote_url, True, url, dir_path)
                    quote_replies_total += quote_replies
                    quotes_spread_total += quotes_with_spread
                    quote_tweets_processed_total += quote_tweets_processed

                if quote_replies_total != -1:
                    logging.info(
                        "---------- Quote scrape successfully done for URL: %s (Phase 3 / 4) ----------\n"
                        "total time: %.2f\n"
                        "time needed: %.2f\n"
                        "total replies in quotes: %d\n"
                        "total quote replies processed: %d\n"
                        "replies in quotes with spread: %d",
                        url, time.time() - start_time, time.time() - processing_quotes_start_time,
                        quote_replies_total, quote_tweets_processed_total, quotes_spread_total)
                else:
                    logging.info("---------- FAILED to process quotes for URL: %s ----------", url)
            process_quotes()

            if not replies_failed:
                def process_users(user_urls: set):
                    users_path = os.path.join(dir_path, "users.csv")
                    user_stuff_start_time = time.time()
                    amount_of_users_successfully_processed = 0
                    for user_url in user_urls:
                        user = get_user_stats(driver, user_url)
                        if not user:
                            print("failed to get user: " + user_url)
                            continue
                        amount_of_users_successfully_processed += 1
                        save_users([user], users_path)

                    logging.info(
                        "---------- Processing users successfully done for URL: %s (Phase 4 / 4) ----------\n"
                        "total time: %.2f\n"
                        "time needed: %.2f\n"
                        "users expected/processed: %d / %d",
                        url, time.time() - start_time, time.time() - user_stuff_start_time, len(user_urls), amount_of_users_successfully_processed)
                process_users(user_urls)

            logging.info(
                "---------- FINISHED SUCCESSFULLY URL: %s ----------",
                url)
        except Exception as e:
            logging.error("Error processing URL: %s", url, exc_info=True)

def create_driver():
    geckodriver_path = os.path.join(os.getcwd(), 'geckodriver.exe')
    service = Service(geckodriver_path)
    options = Options()
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
        driver.switch_to.active_element.send_keys(username)

        # Click "Weiter" to proceed
        next_button = WebDriverWait(driver, 300).until(
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
        final_login_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.XPATH, "(//span[text()='Anmelden'])/ancestor::*[3]"))
        )
        final_login_button.click()
        time.sleep(3)

    def get_login_data():
        def read_login_data():
            login_data = {}
            with open('login_data', 'r') as file:
                for line in file:
                    key, value = line.strip().split('=')
                    login_data[key] = value
            return login_data

        unfiltered_data = read_login_data()

        login_data = [
            {
                'username': unfiltered_data.get('username1'),
                'password': unfiltered_data.get('password1')
            },
            {
                'username': unfiltered_data.get('username2'),
                'password': unfiltered_data.get('password2')
            }
        ]

        for data in login_data:
            if not data['password'] or not data['username']:
                raise ValueError("Username, password, or email is missing in the login_data.txt file.")
        return login_data

    logins = get_login_data()

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(login, driver, logins[i]['username'], logins[i]['password']) for i, driver in enumerate(drivers)]
        for future in futures:
            future.result()

def scraper_task(driver, url_queue, cycle, detailed_folders):
    while not url_queue.empty():
        try:
            url = url_queue.get_nowait()
        except:
            break

        try:
            scrape([url], driver, cycle, detailed_folders)
        finally:
            url_queue.task_done()


def execute_scraping(cycle, urls_to_scrape, detailed_folders):
    url_queue = queue.Queue()
    for url in urls_to_scrape:
        url_queue.put(url)

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(scraper_task, driver1, url_queue, cycle, detailed_folders)
        executor.submit(scraper_task, driver2, url_queue, cycle, detailed_folders)
    url_queue.join()


def load_urls_from_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

driver1 = create_driver()
driver2 = create_driver()
try:
    login_all_drivers([driver1, driver2])

    cycle = 0
    max_cycles = 24
    while cycle < max_cycles:
        urls_to_scrape = load_urls_from_file('urls_to_scrape')
        print(urls_to_scrape)
        print(f"Starting scrape cycle {cycle}")
        start_time = time.time()
        execute_scraping(cycle, urls_to_scrape, False)
        time_needed = time.time() - start_time
        time_to_sleep = max(3600 - time_needed, 0)
        print(f"Cycle {cycle} completed in {time_needed} seconds. Waiting for {time_to_sleep}...")
        sleep(time_to_sleep)
        cycle += 1
finally:
    driver1.quit()
    driver2.quit()

