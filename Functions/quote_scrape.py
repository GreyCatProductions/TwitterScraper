from Functions.Helpers.common_scrape_functions import*
import time
from Functions.Helpers.extractor import *

def get_all_quote_urls(driver, url):
    try:
        link_to_quotes = url + "/quotes"
        print("getting quotes of: " + url)
        driver.get(link_to_quotes)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Timeline: Search timeline"]')))

        urls = set()
        total_quotes_counter = 0

        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        quotes_parent = soup.find(attrs={"aria-label": "Timeline: Search timeline"}).find()
        cycles_since_new_found = 0
        while cycles_since_new_found < 100:
            for current_element in quotes_parent.find_all(recursive=False):
                try:
                    metrics_element, href_element = get_metrics_and_href_element(current_element)
                    href = href_element.get("href")
                    data = metrics_element.get("aria-label")
                    reply_count, repost_count, like_count, bookmark_count, view_count = extract_metrics(data)
                    url = "https://x.com" + normalize_href(href)

                    if url not in urls:
                        cycles_since_new_found = 0
                        total_quotes_counter += 1
                        if reply_count > 0:
                            urls.add(url)
                except Exception as e:
                    continue

            cycles_since_new_found += 1
            print("no new found, scrolling")
            if not scroll(driver, 2000):
                print("scrolling further impossible, ending")
                return list(urls), total_quotes_counter
            time.sleep(1)

        print("no new found in 100 cycles. Ending")
        print("found urls: " + str(len(urls)))
        return list(urls), total_quotes_counter
    except Exception as e:
        print("failed to get quotes for : " + url)
        return -1, -1
