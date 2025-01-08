class User:
    def __init__(self, url: str, description: str, following_count: str, followers_count: str, posts_amount: str):
        self.url = url
        self.description = description
        self.following_count = following_count
        self.followers_count = followers_count
        self.posts_amount = posts_amount

    def get_stats(self):
        return self.url, self.description, self.following_count, self.followers_count, self.posts_amount