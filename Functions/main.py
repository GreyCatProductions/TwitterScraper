from time import sleep
import queue

from Functions.main_scrape_function import scrape
from metricScrapeAdvancedWithLogin import *
from driver_creation import *

#region logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scrape_metrics.log',
    filemode='a'
)
#endregion

def scraper_task(driver, url_queue, cycle, detailed_folders):
    while not url_queue.empty():
        try:
            url = url_queue.get_nowait()
        except:
            break

        try:
            scrape([url], driver, cycle, detailed_folders)
        finally:
            url_queue.task_done()

def execute_scraping(drivers: list[WebDriver], urls_to_scrape: list[str], cycle: int, detailed_folders):
    url_queue = queue.Queue()
    for url in urls_to_scrape:
        url_queue.put(url)

    with ThreadPoolExecutor() as executor:
        for driver in drivers:
            executor.submit(scraper_task, driver, url_queue, cycle, detailed_folders)
    url_queue.join()

def load_urls_from_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

if __name__ == '__main__':
    cycle = 0
    cycles_to_do = 24
    detailed_folders = False
    headless_mode = True

    amount_of_drivers_to_create = 2
    drivers = create_drivers(amount_of_drivers_to_create, headless_mode)
    try:
        login_all_drivers(drivers)

        while cycle < cycles_to_do:
            urls_to_scrape = load_urls_from_file('../urls_to_scrape')
            print(f"All urls loaded: {urls_to_scrape}")
            print(f"Starting scrape cycle {cycle}")

            start_time = time.time()
            execute_scraping(drivers, urls_to_scrape, cycle, detailed_folders)
            time_needed = time.time() - start_time

            time_to_sleep = max(3600 - time_needed, 0)

            print(f"Cycle {cycle} completed in {time_needed} seconds. Waiting for {time_to_sleep}...")

            sleep(time_to_sleep)
            cycle += 1
    finally:
        quit_all_drivers(drivers)

