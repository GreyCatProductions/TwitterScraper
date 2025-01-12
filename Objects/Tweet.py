class Tweet:
    def __init__(self, reply_count: int, repost_count: int, like_count: int, bookmark_count: int, view_count: int, reply_to_url: str, url: str, time_stamp: str, quote_to_url: str, user_url: str):
        self.indirect_view_count = 0
        self.indirect_bookmark_count = 0
        self.indirect_like_count = 0
        self.indirect_repost_count = 0
        self.indirect_reply_count = 0
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

    def get_direct_stats(self):
        return self.reply_count, self.repost_count, self.like_count, self.bookmark_count, self.view_count, self.reply_to_url, self.url, self.time_stamp, self.quote_to_url, self.user_url

    def add_indirect_counts(self, indirect_reply_count: int, indirect_repost_count: int, indirect_like_count: int, indirect_bookmark_count: int, indirect_view_count: int):
        self.indirect_reply_count += indirect_reply_count
        self.indirect_repost_count += indirect_repost_count
        self.indirect_like_count += indirect_like_count
        self.indirect_bookmark_count += indirect_bookmark_count
        self.indirect_view_count += indirect_view_count

    def get_indirect_counts(self):
        return self.indirect_reply_count, self.indirect_repost_count, self.indirect_like_count, self.indirect_bookmark_count, self.indirect_view_count, self.indirect_view_count