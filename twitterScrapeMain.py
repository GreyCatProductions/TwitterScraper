import logging
import time

from metricScrapeNoLogin import *
from metricScrapeAdvancedWithLogin import *
from concurrent.futures import ThreadPoolExecutor

#region logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scrape_metrics.log',
    filemode='a'
)
#endregion

def scrape(urls, driver, cycle):
    def process_tweet_and_replies(url: str, is_root: bool, quote_to: str, extendable_path: str, depth=0, seen_urls = set()):
        retries_left = 10 if is_root else 3

        while retries_left > 0:
            try:
                total_replies_found: int = 0
                tweet, replies,seen_urls = get_tweets(url, driver, is_root, quote_to, seen_urls)

                if tweet is None:
                    print("Failed to fetch tweet" + url)
                    return 0, 0

                try:
                    if len(replies) > 0:
                        save_to_csv_login(replies, total_csv_path)
                except Exception as e:
                    print("SAVING FAILED!!!")
                    logging.error(e)

                if is_root:
                    total_replies_found += tweet.reply_count
                    file_path_og_post = os.path.join(dir_path, "og_post.csv")
                    save_to_csv_login([tweet], total_csv_path)
                    save_to_csv_login([tweet], file_path_og_post)

                replies_found_with_spread = len(replies)

                for i, reply in enumerate(replies):
                    if reply is None:
                        continue
                    reply_dir = os.path.join(extendable_path, str(extract_post_id(reply.url)))
                    os.makedirs(reply_dir, exist_ok=True)
                    reply_post_path = os.path.join(reply_dir, "reply.csv")
                    save_to_csv_login([reply], reply_post_path)

                    if is_root and i % 5 == 0 and i != 0:
                        logging.info(
                            "---Progress Report for Root URL: %s---\nReplies Processed: %d/%d\nReplies With Spread: %d\nTime Spent: %.2f seconds",
                            url, i, len(replies), replies_found_with_spread, time.time() - start_time)

                    if reply.reply_count > 0:
                        sub_replies, sub_spread = process_tweet_and_replies(reply.url, False, "", reply_dir, depth + 1, seen_urls)
                        replies_found_with_spread += sub_spread
                        total_replies_found += reply.reply_count + sub_replies
                return total_replies_found, replies_found_with_spread
            except Exception as e:
                print("failed to scrape tweet: " + url)
                print(e)
                driver.refresh()
                time.sleep(10)
                retries_left -= 1
        return 0, 0

    for url in urls:
        try:
            logging.info("-------------------- SCRAPING: " + url + " --------------------")
            start_time = time.time()
            dir_path = os.path.join("data", str(extract_post_id(url)), str(cycle) + "h")
            total_csv_path = os.path.join(dir_path, "total.csv")
            os.makedirs(dir_path, exist_ok=True)
            replies_total, replies_with_spread_total = process_tweet_and_replies(url,True, "", dir_path)

            quote_urls = get_all_quote_urls(driver, url)

            quote_replies_total, quotes_spread_total = 0, 0
            for quote_url in quote_urls:
                quote_replies, quotes_with_spread = process_tweet_and_replies(quote_url,True, url, dir_path)
                quote_replies_total += quote_replies
                quotes_spread_total += quotes_with_spread

            if replies_total != -1:
                time_needed = time.time() - start_time
                logging.info("---------- Done successfully for URL: %s ----------\ntime needed: %.2f\ntotal_replies: %d\nreplies_with_spread: %d\ntotal_replies_in_quotes: %d\nquotes with spread: %d", url, time_needed, replies_total, replies_with_spread_total,quote_replies_total, quotes_spread_total)
            else:
                logging.info("---------- FAILED for URL: %s ----------", url)
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

def hourly_scrape(url_holder, cycles, time_between_cycles):
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
                    future = executor.submit(scrape, [url], drivers[i], cycle)
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

hourly_scrape("urls_to_scrape", 24, 3600)
