import logging
import time

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

def scrape_with_reply_count(url, minutes_passed):
    try:
        logging.info("Scraping metrics for URL: %s", url)
        reply_count, repost_count, like_count, bookmark_count, view_count = get_metrics_login(url)
        spreading_rate = round((repost_count + reply_count) / view_count * 100, 5) if view_count > 0 else 0

        logging.info(
            "Metrics retrieved: Replies: %d, Reposts: %d, Likes: %d, Bookmarks: %d, Views: %d, Spreading rate: %.5f%%",
            reply_count, repost_count, like_count, bookmark_count, view_count, spreading_rate
        )

        post_id = extract_post_id(url)
        metrics_data = {
            "reply_count": reply_count,
            "repost_count": repost_count,
            "like_count": like_count,
            "bookmark_count": bookmark_count,
            "view_count": view_count,
            "spreading_rate": spreading_rate
        }
        save_to_csv_login(post_id, metrics_data, minutes_passed)

    except Exception as e:
        logging.error("Error scraping metrics for URL: %s", url, exc_info=True)

def hourly_scrape_with_reply_count(url: str, cycles: int, time_between_cycles: int):
    minutes_passed = 0
    while cycles > 0:
        time.sleep(time_between_cycles)
        scrape_with_reply_count(url, minutes_passed)
        minutes_passed += int(time_between_cycles / 60)
        cycles -= 1

hourly_scrape_with_reply_count("https://x.com/TIME/status/1854146717249130998", 72, 3600)
