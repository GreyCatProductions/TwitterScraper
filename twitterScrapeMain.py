import logging
import pandas as pd
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

def scrape_with_reply_count(urls, driver, cycle):
    for url in urls:
        try:
            logging.info("Scraping metrics for URL: %s", url)

            og_tweet, replies = get_metrics_login(url, driver)

            dir_path = os.path.join("data", str(extract_post_id(url)), datetime.now().strftime('%Y-%m-%d'), str(cycle) + "h")

            os.makedirs(dir_path, exist_ok=True)
            file_path_og_post = os.path.join(dir_path, "og_post.csv")
            save_to_csv_login([og_tweet], file_path_og_post)

            for reply in replies:
                reply_dir = os.path.join(dir_path, str(extract_post_id(reply.url)))
                os.makedirs(reply_dir, exist_ok=True)
                reply_post = os.path.join(reply_dir, "reply.csv")
                save_to_csv_login([reply], reply_post)

            logging.info("Done successfully")

        except Exception as e:
            logging.error("Error scraping metrics for URL: %s", url, exc_info=True)

def scrape_replies_of_post(driver, path_of_post):
    df = pd.read_csv(path_of_post)

    post_url = ""
    reply_count = ""

    for index, row in df.iterrows():
        post_url = row["post_url"]
        reply_count = row["reply_count"]

    if reply_count == 0:
        return
    time.sleep(1)
    driver.get(post_url)
    time.sleep(1)

    replies = get_all_replies(driver, post_url)

    for reply in replies:
        reply_dir = os.path.join(path_of_post, str(extract_post_id(reply.url)))
        os.makedirs(reply_dir, exist_ok=True)
        reply_post = os.path.join(reply_dir, "reply.csv")
        save_to_csv_login([reply], reply_post)


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
    "https://x.com/ainyrockstar/status/1857835451807133970"
], 1, 3600, True)
