import os
import csv
from Objects import Tweet, User

def save_tweets(tweets: list[Tweet], path):
    try:
        file_exists = os.path.isfile(path)

        with open(path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(["post url",
                                 "reply to url",
                                 "quote to url",
                                 "user url",
                                 "dir reply count",
                                 "dir repost and quote count",
                                 "dir like count",
                                 "dir bookmark count",
                                 "direct view_count",
                                 "dir spreading_rate",
                                 "dir like affected spreading_rate",
                                 "moment_of_scrape"])

            for tweet in tweets:
                reply_count, repost_count, like_count, bookmark_count, view_count, reply_to_url, url, time_stamp, quote_to_url, user_url = tweet.get_direct_stats()
                dir_spreading_rate = f"{0 if view_count == 0 else round((reply_count + repost_count) / view_count * 100, 3)}%"
                dir_like_affected_spreading_rate = f"{0 if view_count == 0 else round((reply_count + repost_count + like_count) / view_count * 100, 3)}%"

                writer.writerow([
                    url, reply_to_url, quote_to_url, user_url,
                    reply_count,
                    repost_count,
                    like_count,
                    bookmark_count,
                    view_count,
                    dir_spreading_rate, dir_like_affected_spreading_rate,
                    time_stamp
                ])
    except Exception as e:
        raise Exception(f"Failed to save\n{e}")


def save_users(users: list[User], path):
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
    dir_path = os.path.join(dir_path, "tweet_screenshots")
    temp_path = os.path.join(dir_path, "temp.png")
    os.makedirs(dir_path, exist_ok=True)
    try:
        driver.save_screenshot(temp_path)
        return temp_path
    except Exception as e:
        print("Failed to make screenshot of: " +  temp_path)
        print(e)
        return None
