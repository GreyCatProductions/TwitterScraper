from selenium.webdriver.firefox.webdriver import WebDriver

from metricScrapeAdvancedWithLogin import *
from Helpers.saver import *
from quote_scrape import *
from user_scrape import *

#region logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scrape_metrics.log',
    filemode='a'
)
#endregion

def scrape(urls: list[str], driver: WebDriver, cycle: int, detailed_folders: bool):
    for url in urls:
        try:
            logging.info("-------------------- SCRAPING: " + url + " --------------------")
            start_time = time.time()
            hour_path = os.path.join("data", str(extract_post_id(url)), str(cycle) + "h")
            total_csv_path = os.path.join(hour_path, "total.csv")
            os.makedirs(hour_path, exist_ok=True)

            user_urls = process_replies(driver, total_csv_path, hour_path, detailed_folders, start_time, url)
            replies_processed_successfully = len(user_urls) == 0

            quotes_processes_successfully = process_quotes(driver, total_csv_path, hour_path, detailed_folders, start_time, url)

            users_processed_successfully = 0
            if not replies_processed_successfully:
                users_processed_successfully = process_users(user_urls)

            logging.info(
                f"---------- FINISHED SCRAPING URL: {url} ----------\n"
                f"total time: {round(time.time() - start_time, 2)}s\n"
                f"replies processed successfully: {replies_processed_successfully}\n"
                f"quotes processed successfully: {quotes_processes_successfully}\n"
                f"users processed successfully: {users_processed_successfully} / {len(user_urls)}\n")
        except Exception as e:
            logging.error("Failed to process URL: %s", url, exc_info=True)

def process_replies(driver:WebDriver, total_csv_path: str, hour_path: str, detailed_folders: bool, start_time: float, url: str) -> list[str]:
    replies_total, replies_with_spread_total, user_urls, tweets_processed = process_tweet_and_its_replies(
        driver=driver,
        total_csv_path=total_csv_path,
        hour_final_path=hour_path,
        dir_path=hour_path,
        detailed_folders=detailed_folders,
        start_time=start_time,
        url_to_process=url,
        is_root=True,
        quote_to_url="",
        extendable_path=hour_path,
        depth=0,
        seen_urls=set(),
        users=set(),
        total_replies_processed=0)
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
        return []

    return user_urls

def process_quotes(driver: WebDriver, total_csv_path: str, hour_path: str, detailed_folders: bool, start_time: float, url: str):
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
        return False

    processing_quotes_start_time = time.time()
    quote_replies_total = quotes_spread_total = quote_tweets_processed_total = 0
    for quote_url in quote_urls_with_spread:
        quote_replies, quotes_with_spread, quote_users, quote_tweets_processed = process_tweet_and_its_replies(
            driver=driver,
            total_csv_path=total_csv_path,
            hour_final_path=hour_path,
            dir_path=hour_path,
            detailed_folders=detailed_folders,
            start_time=start_time,
            url_to_process=quote_url,
            is_root=True,
            quote_to_url=url,
            extendable_path=hour_path,
            depth=0,
            seen_urls=set(),
            users=set(),
            total_replies_processed=0)

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
        return False
    return True

def process_tweet_and_its_replies(
        driver: WebDriver,
        total_csv_path: str,
        hour_final_path: str,
        dir_path: str,
        detailed_folders: bool,
        start_time: float,
        url_to_process: str,
        is_root: bool,
        quote_to_url: str,
        extendable_path: str,
        depth: int,
        seen_urls: set,
        users: set,
        total_replies_processed: int) -> (int, int, set, int):

    retries_left = 10 if is_root else 3

    while retries_left > 0:
        try:
            total_replies_found = 0

            tweet, replies, seen_urls = get_tweets(url_to_process, driver, is_root, quote_to_url, seen_urls,
                                                   hour_final_path)

            if tweet is None:
                print(f"Failed to scrape tweet: {url_to_process}")
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
                        f"--- Progress Report for Root URL: {url_to_process} ---\n"
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

                        sub_replies, sub_spread, sub_users, sub_processed = process_tweet_and_its_replies(
                            driver=driver,
                            total_csv_path=total_csv_path,
                            hour_final_path=hour_final_path,
                            dir_path=dir_path,
                            detailed_folders=detailed_folders,
                            start_time=start_time,
                            url_to_process=reply.url,
                            is_root=False,
                            quote_to_url="",
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
            print(f"Failed to scrape tweet: {url_to_process}")
            print(main_error)
            driver.refresh()
            time.sleep(10)
            retries_left -= 1

    return 0, 0, users, total_replies_processed


def process_users(driver: WebDriver, dir_path: str, start_time: float, og_url: str, user_urls: set) -> int:
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
        og_url, time.time() - start_time, time.time() - user_stuff_start_time, len(user_urls),
        amount_of_users_successfully_processed)
    return amount_of_users_successfully_processed