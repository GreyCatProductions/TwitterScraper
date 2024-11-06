import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import time
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
                count_value = int(re.sub(r"[^\d]", "", count_text))

            return int(count_value)

    return None

def extract_post_id(url: str) -> str:
    return urlparse(url).path.split('/')[-1]

def save_to_csv_login(post_id: str, data: dict, time_stamp: int):
    date_str = datetime.now().strftime('%Y-%m-%d')
    dir_path = os.path.join("data", post_id, date_str)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "data.csv")

    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["minutes since upload, reply_count, repost_count, like_count, bookmark_count, view_count, spreading_rate"])
        writer.writerow([time_stamp, data["reply_count"], data["repost_count"], data["like_count"], data["bookmark_count"], data["view_count"], data["spreading_rate"]])
