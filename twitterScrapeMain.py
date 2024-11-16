import logging

from commonMethods import *
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

def scrape_with_reply_count(urls, driver, all_layers, cycle):
    for url in urls:
        try:
            logging.info("Scraping metrics for URL: %s", url)
            og_tweet, replies = get_metrics_login(url, driver, all_layers)

            dir_path = os.path.join("data", str(extract_post_id(url)), datetime.now().strftime('%Y-%m-%d'))
            replies_path = os.path.join(dir_path, str(cycle) + "h")
            os.makedirs(dir_path, exist_ok=True)
            os.makedirs(replies_path, exist_ok=True)
            file_path_og_post = os.path.join(dir_path, "og_post.csv")
            file_path_replies = os.path.join(replies_path, "replies.csv")
            save_to_csv_login(file_path_og_post, file_path_replies, og_tweet, replies)

            logging.info("Done successfully")

        except Exception as e:
            logging.error("Error scraping metrics for URL: %s", url, exc_info=True)

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
            scrape_with_reply_count(urls, driver, all_layers, cycle)
            time_used_for_scraping = time.time() - scrape_start

            minutes_passed += int(time_between_cycles / 60)

            time.sleep(time_between_cycles - time_used_for_scraping)
    finally:
        driver.quit()


hourly_scrape([
    "https://x.com/snicklink/status/1857459707524366386"
], 1, 3600, True)