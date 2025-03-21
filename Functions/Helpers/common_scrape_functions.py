import re
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def wait_until_loaded(driver, x_path, time_to_wait):
    WebDriverWait(driver, time_to_wait).until(
        EC.presence_of_element_located((By.XPATH, x_path))
    )

def check_if_page_exists(driver):
    try:
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Hmm...this page doesn’t exist. Try searching for something else.']")))
        return False
    except Exception:
        return True

def get_metrics_and_href_element(parent_element):
    metrics_element = parent_element.find(attrs={"role": "group"})
    if metrics_element is None:
        raise Exception("Metrics element not found")
    href_element = parent_element.find(
        lambda tag: tag.get("role") == "link"
                    and re.match(r".*/status/\d+.*", tag.get("href", ""))
                    and (tag.has_attr("aria-describedby") or tag.has_attr("aria-label"))
    )

    if href_element is None:
        raise Exception("Href element not found")
    return metrics_element, href_element

def scroll(driver, y_range):
    current_scroll = driver.execute_script("return window.scrollY;")
    time.sleep(0.1)

    max_scroll = driver.execute_script("return document.body.scrollHeight - window.innerHeight;")
    driver.execute_script(f"window.scrollBy(0, {y_range});")

    new_scroll = driver.execute_script("return window.scrollY;")

    return new_scroll != current_scroll and new_scroll < max_scroll

