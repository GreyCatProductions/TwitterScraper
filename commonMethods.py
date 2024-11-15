import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import csv
from datetime import datetime

def extract_count(soup: BeautifulSoup, metric_name: str) -> int:
    data = soup.find(string=re.compile(metric_name))
    if data:
        parent = data.find_parent().find_parent().find_parent()
        count_span = parent.find('div').find('span').find('span').find('span')

        if count_span:
            count_text = count_span.text.strip()
            if "Mio." in count_text:
                count_text = count_text.replace("Mio.", "").strip()
                count_value = float(count_text.replace(",", ".")) * 1_000_000
            elif "K" in count_text:
                count_text = count_text.replace("K", "").strip()
                count_value = float(count_text.replace(",", ".")) * 1_000
            else:
                count_value = int(re.sub(r"\D", "", count_text))

            return int(count_value)

    return None

def extract_post_id(url: str) -> int:
    return int(urlparse(url).path.split('/')[-1])

def save_to_csv_login(file_path_og_post, file_path_replies, og_tweet, replies):
    def write_data(file_exists, tweets: [Tweet], file):
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["time_since_upload",
                             "post_url",
                             "reply_count",
                             "repost_count",
                             "like_count",
                             "bookmark_count",
                             "view_count",
                             "reply_to_id",
                             "spreading_rate %"])

        for tweet in tweets:
            reply_count, repost_count, like_count, bookmark_count, view_count, reply_to_id, time_since_upload, url = tweet.get_stats()
            writer.writerow(
                [time_since_upload, url, reply_count, repost_count, like_count, bookmark_count, view_count, reply_to_id, 0 if view_count == 0 else (reply_count + repost_count) / view_count * 100])

    file_exists_og_post = os.path.isfile(file_path_og_post)
    file_exists_replies = os.path.isfile(file_path_replies)

    try:
        with open(file_path_og_post, mode='a', newline='', encoding='utf-8') as file_og_post, \
             open(file_path_replies, mode='a', newline='', encoding='utf-8') as file_replies:
            write_data(file_exists_og_post, [og_tweet], file_og_post)
            write_data(file_exists_replies, replies, file_replies)
    except OSError as e:
        print(f"Error opening or writing to file: {e}")

def twitter_time_to_python_time(datetime_str: str) -> float:
    try:
        print("parsing:" + datetime_str)
        parsed_datetime = datetime.strptime(datetime_str, "%I:%M %p · %b %d, %Y")
    except Exception as e:
        print(e)
        return 0
    return parsed_datetime.timestamp()

class Tweet:
    def __init__(self, reply_count, repost_count, like_count, bookmark_count, view_count, reply_to_id, time_since_upload, url):
        self.reply_count = reply_count
        self.repost_count = repost_count
        self.like_count = like_count
        self.bookmark_count = bookmark_count
        self.view_count = view_count
        self.reply_to_id= reply_to_id
        self.time_since_upload = time_since_upload
        self.url = url

    def get_stats(self):
        return self.reply_count, self.repost_count, self.like_count, self.bookmark_count, self.view_count, self.reply_to_id, self.time_since_upload, self.url
