from commonMethods import *
import time


def get_user_stats(driver, user_url: str): #expects logged in and open driver
    time.sleep(1)
    driver.get(user_url)
    time.sleep(1)
    print("Getting user data for: " + user_url)

    if not check_if_page_exists(driver):
        return

    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    profile_parent = soup.find(attrs={"aria-label": "Home timeline"})

    post_count = profile_parent.find('h2').find_next_sibling().text

    description_parent = profile_parent.find(attrs={"data-testid":"UserDescription"})
    description = ""
    for child in description_parent.find(recursive=False):
        if child.name == "span":
            description += child.text

    followers_count = profile_parent.find('a', href=lambda x: x and "/verified_followers" in x).find().find().text
    following_count = profile_parent.find('a', href=lambda x: x and "/following" in x).find().find().text

    user = User(user_url, description, following_count, followers_count, post_count)
    return user