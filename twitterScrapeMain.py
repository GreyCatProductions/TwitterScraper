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

def scrape_with_reply_count(urls, driver, cycle):
    def process_tweet_and_replies(url, dir_path, is_root, seen_urls):
        try:
            logging.info("Scraping metrics for URL: %s", url)

            og_tweet, replies, seen_urls = get_metrics_login(url, driver, seen_urls)

            if is_root:
                logging.info("root_post done: " + og_tweet.url)
                file_path_og_post = os.path.join(dir_path, "og_post.csv")
                save_to_csv_login([og_tweet], file_path_og_post)

            for reply in replies:
                reply_dir = os.path.join(dir_path, str(extract_post_id(reply.url)))
                os.makedirs(reply_dir, exist_ok=True)

                reply_post_path = os.path.join(reply_dir, "reply.csv")
                save_to_csv_login([reply], reply_post_path)

                if reply.reply_count > 0:
                    process_tweet_and_replies(reply.url, reply_dir, False, seen_urls)

        except Exception as e:
            logging.error("Error scraping metrics for URL: %s", url, exc_info=True)

    for url in urls:
        try:
            logging.info("---------- SCRAPING: " + url + " -------------")
            seen_urls = set()
            dir_path = os.path.join(
                "data",
                str(extract_post_id(url)),
                datetime.now().strftime('%Y-%m-%d'),
                str(cycle) + "h"
            )
            os.makedirs(dir_path, exist_ok=True)

            process_tweet_and_replies(url, dir_path, True, seen_urls)
            logging.info("Done successfully for URL: %s", url)

        except Exception as e:
            logging.error("Error processing URL: %s", url, exc_info=True)

def hourly_scrape(urls: [str], cycles: int, time_between_cycles: int, all_layers: bool):
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
            scrape_start = time.time()
            scrape_with_reply_count(urls, driver, cycle)
            time_used_for_scraping = time.time() - scrape_start

            minutes_passed += int(time_between_cycles / 60)

            time.sleep(time_between_cycles - time_used_for_scraping)
    finally:
        driver.quit()


hourly_scrape([
    "https://x.com/BRICSinfo/status/1859790766413054168", "https://x.com/elonmusk/status/1859824059464417372", "https://x.com/AHuxley1963/status/1859844687525445844", "https://x.com/justdana1818/status/1859578661860475016", "https://x.com/EndWokeness/status/1859818323598508425", "https://x.com/EndWokeness/status/1859679069677507061", "https://x.com/HeimatliebeDE/status/1859302620290220234"
], 1, 3600, True)
