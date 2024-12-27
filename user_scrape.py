from bs4 import Tag, NavigableString
import time

from selenium.common import TimeoutException

from commonMethods import *

def get_user_stats(driver, user_url: str):  # Expects logged in and open driver
    max_retries = 5
    while max_retries > 0:
        try:
            time.sleep(1)
            driver.get(user_url)
            try:
                wait_until_loaded(driver, '//*[@aria-label="Home timeline"]', 10)
            except TimeoutException:
                max_retries -= 1
                print("cant get user data. Refreshing and waiting 60 seconds")
                time.sleep(60)
                continue

            time.sleep(1)

            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'html.parser')
            profile_parent = soup.find(attrs={"aria-label": "Home timeline"})

            if not profile_parent:
                print("Profile parent not found.")

            post_count = None
            post_count_header = profile_parent.find('h2')
            if post_count_header:
                sibling = post_count_header.find_next_sibling()
                post_count = sibling.text if sibling else None

            description_parent = profile_parent.find('div', {'data-testid': 'UserDescription'})
            description = []

            if description_parent:
                for child in description_parent.children:
                    if isinstance(child, Tag):
                        if child.name == 'span':
                            description.append(child.get_text(strip=True))
                        elif child.name == 'img' and child.get('alt'):
                            description.append(child['alt'])
                    elif isinstance(child, NavigableString):
                        description.append(str(child).strip())

            description = ' '.join(description)

            followers_count = None
            following_count = None

            followers_element = profile_parent.find('a', href=lambda x: x and "/verified_followers" in x)
            if followers_element:
                followers_count = followers_element.text.strip()

            following_element = profile_parent.find('a', href=lambda x: x and "/following" in x)
            if following_element:
                following_count = following_element.text.strip()

            user = User(user_url, description, following_count, followers_count, post_count)
            return user
        except TimeoutException: #happens when side does not load properly for some reason. Fixed by simple refresh
            max_retries -= 1
            print("cant get user data. Refreshing.")
            time.sleep(3)
        except Exception as e:
            print(f"Error while getting user stats: {e}")
            return None
