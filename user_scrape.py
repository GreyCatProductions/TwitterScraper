from bs4 import Tag, NavigableString
import time
from commonMethods import *

def get_user_stats(driver, user_url: str):  # Expects logged in and open driver
    try:
        time.sleep(1)
        driver.get(user_url)
        time.sleep(1)

        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        profile_parent = soup.find(attrs={"aria-label": "Home timeline"})

        if not profile_parent:
            print("Profile parent not found.")
            return None

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

        try:
            followers_element = profile_parent.find('a', href=lambda x: x and "/verified_followers" in x)
            if followers_element:
                followers_count = followers_element.text.strip()

            following_element = profile_parent.find('a', href=lambda x: x and "/following" in x)
            if following_element:
                following_count = following_element.text.strip()
        except AttributeError:
            print("Failed to extract followers/following counts.")

        user = User(user_url, description, following_count, followers_count, post_count)
        return user

    except Exception as e:
        print(f"Error while getting user stats: {e}")
        return None
