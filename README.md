Twitter Scraper to get full spreading data of a tweet. 
Input is a tweet.
Output is a .csv with all replies, replies of replies etc.; quotes, their replies etc.; all users and some of their public profile data

How to use:
1. In main.py change the parameters as you wish them to be. 
2. Fill login_data with as much username-login pairs as you selected in main.py. The default is 3
3. Copy paste the urls of the tweets you want scraped into urls_to_scrape.txt
4. Start main.py
5. You can add new urls to urls_to_scrape.txt between the cycles. 

Important:
- If not headless:
  - Keep the windows at full size to prevent weird format bugs and bad screenshot formats
  - Do not touch the windows at all until the login is done
  - If you see the cat image it means the driver is idle