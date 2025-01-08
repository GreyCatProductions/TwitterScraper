class Tweet:
    def __init__(self, reply_count: int, repost_count: int, like_count: int, bookmark_count: int, view_count: int, reply_to_url: str, url: str, time_stamp: str, quote_to_url: str, user_url: str):
        self.reply_count = reply_count
        self.repost_count = repost_count
        self.like_count = like_count
        self.bookmark_count = bookmark_count
        self.view_count = view_count
        self.reply_to_url = reply_to_url
        self.url = url
        self.time_stamp = time_stamp,
        self.quote_to_url = quote_to_url
        self.user_url = user_url

    def get_stats(self):
        return self.reply_count, self.repost_count, self.like_count, self.bookmark_count, self.view_count, self.reply_to_url, self.url, self.time_stamp, self.quote_to_url, self.user_url
