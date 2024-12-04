import logging
from metricScrapeNoLogin import *
from metricScrapeAdvancedWithLogin import *

#region logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scrape_metrics.log',
    filemode='a'
)
#endregion

def scrape(urls, driver, cycle):
    def process_tweet_and_replies(url, is_root, seen_urls, extendable_path):
        retries_left = 10 if is_root else 3
        while retries_left > 0:
            try:
                logging.info("Scraping metrics for URL: %s", url)

                og_tweet, replies, seen_urls = get_metrics_login(url, driver, seen_urls, is_root)

                if og_tweet is None and replies is None:
                    logging.info("URL: %s GOT LIKELY DELETED", url)
                    return False

                total_csv_path = os.path.join(dir_path, "total.csv")
                save_to_csv_login(replies, total_csv_path)

                if is_root:
                    logging.info("root_post done: " + og_tweet.url)
                    file_path_og_post = os.path.join(dir_path, "og_post.csv")
                    save_to_csv_login([og_tweet], file_path_og_post)

                for reply in replies:
                    reply_dir = os.path.join(extendable_path, str(extract_post_id(reply.url)))
                    os.makedirs(reply_dir, exist_ok=True)
                    reply_post_path = os.path.join(reply_dir, "reply.csv")
                    save_to_csv_login([reply], reply_post_path)

                    if reply.reply_count > 0:
                        process_tweet_and_replies(reply.url, False, seen_urls, reply_dir)
                return True
            except Exception as e:
                logging.error("Error scraping metrics for URL: %s", url, exc_info=True)
                driver.refresh()
                time.sleep(10)
                retries_left -= 1
        return False

    for url in urls:
        try:
            logging.info("---------- SCRAPING: " + url + " -------------")
            seen_urls = set()
            dir_path = os.path.join("data", str(extract_post_id(url)), str(cycle) + "h")
            os.makedirs(dir_path, exist_ok=True)
            if process_tweet_and_replies(url,True, seen_urls, dir_path):
                logging.info("---------- Done successfully for URL: %s ----------", url)
            else:
                logging.info("---------- FAILED for URL: %s ----------", url)

        except Exception as e:
            logging.error("Error processing URL: %s", url, exc_info=True)

def hourly_scrape(url_holder, cycles, time_between_cycles):
    driver = None
    try:
        #region preparing the driver and logging in
        geckodriver_path = os.path.join(os.getcwd(), 'geckodriver.exe')
        service = Service(geckodriver_path)
        options = Options()
        #options.add_argument("--headless")
        driver = webdriver.Firefox(service=service, options=options)
        driver.maximize_window()
        #login needed
        login(driver)
        #endregion

        minutes_passed = 0

        for cycle in range(cycles):
            logging.info("Cycle %d/%d starting", cycle + 1, cycles)
            urls = load_urls_from_file(url_holder)
            scrape_start = time.time()
            scrape(urls, driver, cycle)
            time_used_for_scraping = time.time() - scrape_start

            minutes_passed += int(time_between_cycles / 60)

            time.sleep(time_between_cycles - time_used_for_scraping - 60)
            print("Next Cycle starting in 60 seconds. Do not work on urls_to_scrape!!!")
            time.sleep(60)
    finally:
        driver.quit()

def load_urls_from_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

hourly_scrape("urls_to_scrape", 24, 3600)
