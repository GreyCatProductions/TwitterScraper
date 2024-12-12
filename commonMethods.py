import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import csv

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
                             "reply_to_url",
                             "quote_to_url",
                             "moment_of_scrape",
                             "reply_count",
                             "repost_count",
                             "like_count",
                             "bookmark_count",
                             "view_count",
                             "spreading_rate in %"])

        for tweet in tweets:
            reply_count, repost_count, like_count, bookmark_count, view_count, reply_to_url, url, time_stamp, quote_to_url = tweet.get_stats()
            spreading_rate = 0 if view_count == 0 else round((reply_count + repost_count) / view_count * 100, 3)
            writer.writerow([url, reply_to_url, quote_to_url, time_stamp, reply_count, repost_count, like_count, bookmark_count, view_count, spreading_rate])

def get_metrics(data_text: str) -> tuple: #expects data.get('aria label'....)
    replies_match = re.search(r"(\d+)\s+replies", data_text)
    reposts_match = re.search(r"(\d+)\s+reposts", data_text)
    likes_match = re.search(r"(\d+)\s+likes", data_text)
    bookmarks_match = re.search(r"(\d+)\s+bookmarks", data_text)
    views_match = re.search(r"(\d+)\s+views", data_text)

    reply_count = repost_count = like_count = bookmark_count = view_count = 0

    if replies_match:
        reply_count = int(replies_match.group(1))
    if reposts_match:
        repost_count = int(reposts_match.group(1))
    if likes_match:
        like_count = int(likes_match.group(1))
    if bookmarks_match:
        bookmark_count = int(bookmarks_match.group(1))
    if views_match:
        view_count = int(views_match.group(1))
    return reply_count, repost_count, like_count, bookmark_count, view_count

class Tweet:
    def __init__(self, reply_count: int, repost_count: int, like_count: int, bookmark_count: int, view_count: int, reply_to_url: str, url: str, time_stamp: str, quote_to_url: str):
        self.reply_count = reply_count
        self.repost_count = repost_count
        self.like_count = like_count
        self.bookmark_count = bookmark_count
        self.view_count = view_count
        self.reply_to_url = reply_to_url
        self.url = url
        self.time_stamp = time_stamp,
        self.quote_to_url = quote_to_url

    def get_stats(self):
        return self.reply_count, self.repost_count, self.like_count, self.bookmark_count, self.view_count, self.reply_to_url, self.url, self.time_stamp, self.quote_to_url
