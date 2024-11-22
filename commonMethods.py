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
    else:
        print("FAILED TO GET DATA!")
    return -1

def extract_post_id(url: str) -> int:
    return int(urlparse(url).path.split('/')[-1])

def save_to_csv_login(tweets, path):
    file_exists = os.path.isfile(path)
    with open(path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["post_url",
                             "reply_count",
                             "repost_count",
                             "like_count",
                             "bookmark_count",
                             "view_count",
                             "reply_to_id",
                             "spreading_rate %"])

        for tweet in tweets:
            reply_count, repost_count, like_count, bookmark_count, view_count, reply_to_id, url = tweet.get_stats()
            spreading_rate = 0 if view_count == 0 else (reply_count + repost_count) / view_count * 100
            writer.writerow(
                [url, reply_count, repost_count, like_count, bookmark_count, view_count, reply_to_id,
                 spreading_rate])


def twitter_time_to_python_time(datetime_str: str) -> float:
    try:
        print("parsing:" + datetime_str)
        parsed_datetime = datetime.strptime(datetime_str, "%I:%M %p · %b %d, %Y")
    except Exception as e:
        print(e)
        return 0
    return parsed_datetime.timestamp()

class Tweet:
    def __init__(self, reply_count: int, repost_count: int, like_count: int, bookmark_count: int, view_count: int, reply_to_url: str, url: str):
        self.reply_count = reply_count
        self.repost_count = repost_count
        self.like_count = like_count
        self.bookmark_count = bookmark_count
        self.view_count = view_count
        self.reply_to_id= reply_to_url
        self.url = url

    def get_stats(self):
        return self.reply_count, self.repost_count, self.like_count, self.bookmark_count, self.view_count, self.reply_to_id, self.url
