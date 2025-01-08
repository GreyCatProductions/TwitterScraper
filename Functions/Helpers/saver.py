import os
import csv

def save_tweets(tweets, path):
    file_exists = os.path.isfile(path)
    with open(path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["post_url",
                             "reply_to_url",
                             "quote_to_url",
                             "user_url",
                             "moment_of_scrape",
                             "reply_count",
                             "repost_count",
                             "like_count",
                             "bookmark_count",
                             "view_count",
                             "spreading_rate in %",
                             #like inspired
                                ])

        for tweet in tweets:
            reply_count, repost_count, like_count, bookmark_count, view_count, reply_to_url, url, time_stamp, quote_to_url, user_url = tweet.get_stats()
            spreading_rate = 0 if view_count == 0 else round((reply_count + repost_count) / view_count * 100, 3)
            writer.writerow([url, reply_to_url, quote_to_url, user_url, time_stamp, reply_count, repost_count, like_count, bookmark_count, view_count, spreading_rate])

def save_users(users, path):
    file_exists = os.path.isfile(path)
    with open(path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["user_url",
                             "user_description",
                             "following_count",
                             "followers_count",
                             "posts_amount"])

        for user in users:
            url, description, following_count, followers_count, posts_amount = user.get_stats()
            writer.writerow([url, description, following_count, followers_count, posts_amount])

def make_and_save_screenshot(driver, dir_path):
    try:
        dir_path = os.path.join(dir_path, "tweet_screenshots")
        temp_path = os.path.join(dir_path, "temp.png")
        os.makedirs(dir_path, exist_ok=True)
        driver.save_screenshot(temp_path)
        return temp_path
    except Exception as e:
        print("Failed to make screenshot of: " +  temp_path)
        print(e)
        return None
