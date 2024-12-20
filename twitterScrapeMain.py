import logging
from metricScrapeNoLogin import *
from metricScrapeAdvancedWithLogin import *
from concurrent.futures import ThreadPoolExecutor
from user_scrape import *

#region logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scrape_metrics.log',
    filemode='a'
)
#endregion

def scrape(urls, driver, cycle, detailed_folders):
    def process_tweet_and_replies(url: str, is_root: bool, quote_to: str, extendable_path: str, depth: int = 0, seen_urls: set = set(), users: set = set()): #used by process replies and process quotes
        retries_left = 10 if is_root else 3

        while retries_left > 0:
            try:
                total_replies_found: int = 0
                tweet, replies,seen_urls = get_tweets(url, driver, is_root, quote_to, seen_urls, hour_final_path)

                if tweet is None:
                    print("Failed to fetch tweet" + url)
                    return 0, 0, users

                try:
                    if len(replies) > 0:
                        save_tweets(replies, total_csv_path)
                except Exception as e:
                    print("SAVING FAILED!!!")
                    logging.error(e)

                if is_root:
                    total_replies_found += tweet.reply_count
                    users.add(tweet.user_url)
                    file_path_og_post = os.path.join(dir_path, "og_post.csv")
                    save_tweets([tweet], total_csv_path)
                    if detailed_folders:
                        save_tweets([tweet], file_path_og_post)

                replies_found_with_spread = len(replies)

                for i, reply in enumerate(replies):
                    if reply is None:
                        continue

                    reply_dir = os.path.join(extendable_path, str(extract_post_id(reply.url)))

                    if detailed_folders:
                        os.makedirs(reply_dir, exist_ok=True)
                        reply_post_path = os.path.join(reply_dir, "reply.csv")
                        save_tweets([reply], reply_post_path)

                    if is_root and i % 5 == 0 and i != 0:
                        logging.info(
                            "---Progress Report for Root URL: %s---\nTotal replies processed: %d\nFirst Layer Replies Processed: %d/%d\nReplies With Spread: %d\nTime Spent: %.2f seconds\nAverage time per post: %.2f seconds\n",
                            url, total_replies_found, i, len(replies), replies_found_with_spread, time.time() - start_time, (time.time() - start_time) / replies_found_with_spread)

                    if reply.reply_count > 0:
                        try:
                            users.add(reply.user_url)
                            sub_replies, sub_spread, sub_users = process_tweet_and_replies(reply.url, False, "", reply_dir, depth + 1, seen_urls, users)
                            users.update(sub_users)
                            replies_found_with_spread += sub_spread
                            total_replies_found += reply.reply_count + sub_replies
                        except Exception as e:
                            print("failed to process reply: " + reply.url)
                            print(e)
                            continue
                return total_replies_found, replies_found_with_spread, users
            except Exception as e:
                print("failed to scrape tweet: " + url)
                print(e)
                driver.refresh()
                time.sleep(10)
                retries_left -= 1
        return 0, 0, users

    for url in urls:
        try:
            logging.info("-------------------- SCRAPING: " + url + " --------------------")
            start_time = time.time()
            dir_path = os.path.join("data", str(extract_post_id(url)), str(cycle) + "h")
            total_csv_path = os.path.join(dir_path, "total.csv")
            hour_final_path = dir_path
            os.makedirs(dir_path, exist_ok=True)

            def process_replies():
                replies_total, replies_with_spread_total, user_urls = process_tweet_and_replies(url, True, "", dir_path)
                if replies_total != -1:
                    logging.info(
                        "---------- Reply scrape successfully done for URL: %s (Phase 1 / 4) ----------\ntime needed: %.2f\ntotal replies: %d\nreplies with spread: %d\namount_of unique users: %d",
                        url, time.time() - start_time, replies_total, replies_with_spread_total, len(user_urls))
                else:
                    logging.info("---------- FAILED to get replies for URL: %s ----------", url)
                    return None

                return user_urls
            user_urls = process_replies()
            replies_failed = user_urls is None

            def process_quotes():
                # getting quotes
                getting_quotes_start_time = time.time()
                quote_urls_with_spread, total_quotes_count = get_all_quote_urls(driver, url)
                if quote_urls_with_spread != -1:
                    logging.info(
                        "---------- Getting all quotes successfully done for URL: %s (Phase 2 / 4) ----------\ntotal time: %.2f\ntime needed: %.2f\ntotal quotes found: %d \nquotes with spread found: %d",
                        url, time.time() - start_time, time.time() - getting_quotes_start_time, total_quotes_count,
                        len(quote_urls_with_spread))
                else:
                    logging.info("---------- FAILED to get quotes for URL: %s ----------", url)
                    return

                # processing quotes
                processing_quotes_start_time = time.time()
                quote_replies_total, quotes_spread_total = 0, 0
                for quote_url in quote_urls_with_spread:
                    quote_replies, quotes_with_spread, quote_users = process_tweet_and_replies(quote_url, True, url,
                                                                                               dir_path)
                    quote_replies_total += quote_replies
                    quotes_spread_total += quotes_with_spread

                if quote_replies_total != -1:
                    logging.info(
                        "---------- Quote scrape successfully done for URL: %s (Phase 3 / 4) ----------\ntotal time: %.2f\ntime needed: %.2f\ntotal replies in quotes: %d\nreplies in quotes with spread: %d",
                        url, time.time() - start_time, time.time() - processing_quotes_start_time,
                        quote_replies_total, quotes_spread_total)
                else:
                    logging.info("---------- FAILED to process quotes for URL: %s ----------", url)
            process_quotes()

            if not replies_failed:
                def process_users(user_urls: set):
                    users_path = os.path.join(dir_path, "users.csv")
                    user_stuff_start_time = time.time()
                    for user_url in user_urls:
                        user = get_user_stats(driver, user_url)
                        if not user:
                            print("failed to get user: " + user_url)
                            continue
                        save_users([user], users_path)

                    logging.info(
                        "---------- Processing users successfully done for URL: %s (Phase 4 / 4) ----------\ntotal time: %.2f\ntime needed: %.2f",
                        url, time.time() - start_time, time.time() - user_stuff_start_time)
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
    #options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)
    driver.maximize_window()
    return driver


def login_all_drivers(drivers):
    def login_driver(driver):
        try:
            login(driver)
        except Exception as e:
            raise e

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(login_driver, driver) for driver in drivers]
        for future in futures:
            future.result()

def hourly_scrape(url_holder, cycles, time_between_cycles, detailed_folders):
    urls = load_urls_from_file(url_holder)
    with ThreadPoolExecutor(max_workers=5) as executor:
        try:
            drivers = [create_driver() for _ in range(len(urls))]
            print("Logging in all drivers...")
            login_all_drivers(drivers)
            print("All drivers logged in successfully.")

            for cycle in range(cycles):
                logging.info("Cycle %d/%d starting", cycle + 1, cycles)
                cycle_start_time = time.time()

                processes = []
                for i, url in enumerate(urls):
                    start_time = time.time()
                    future = executor.submit(scrape, [url], drivers[i], cycle, detailed_folders)
                    processes.append((future, start_time, url))

                for future, start_time, url in processes:
                    future.result()

                cycle_duration = time.time() - cycle_start_time
                if cycle < cycles - 1:
                    sleep_time = max(0, time_between_cycles - cycle_duration)
                    time.sleep(sleep_time)
        finally:
            for driver in drivers:
                driver.quit()


def load_urls_from_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

hourly_scrape("urls_to_scrape", 24, 3600, False)
