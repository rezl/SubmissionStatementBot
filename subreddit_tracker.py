from datetime import datetime


class SubredditTracker:
    def __init__(self, subreddit, settings):
        self.subreddit = subreddit
        self.subreddit_name = subreddit.display_name
        self.time_unmoderated_last_checked = datetime.utcfromtimestamp(0)
        self.monitored_ss_replies = list()
        self.settings = settings
