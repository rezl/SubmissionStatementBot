import time
import traceback

from settings import Settings
from praw.exceptions import RedditAPIException


class RedditActionsHandler:
    max_retries = 3
    retry_delay_secs = 10

    def __init__(self, reddit, discord_client):
        self.reddit = reddit
        self.discord_client = discord_client
        self.last_call_time = 0

    def remove_content(self, content, external_removal_reason, internal_removal_reason, reply=True):
        print(f"\tRemoving content {content}, reason: {internal_removal_reason}")
        self.reddit_call(lambda: content.mod.remove(mod_note=internal_removal_reason))
        if reply:
            self.reply_to_content(content, external_removal_reason)

    def report_content(self, content, reason):
        print(f"\tReporting content {content}, reason: {reason}")
        self.reddit_call(lambda: content.report(reason))

    def reply_to_content(self, content, reason, pin=True, lock=False, ignore_reports=False):
        print(f"\tReplying to content, reason: {reason}")
        max_chars = 10000
        if len(reason) > max_chars:
            print(f"Warning: Reason has been truncated to {max_chars} characters")
            reason = reason[:max_chars]
        reply_comment = self.reddit_call(lambda: content.reply(reason))
        self.reddit_call(lambda: reply_comment.mod.distinguish(sticky=pin), reddit_throttle_secs=1)
        if lock:
            self.reddit_call(lambda: reply_comment.mod.lock(), reddit_throttle_secs=1)
        if ignore_reports:
            self.reddit_call(lambda: reply_comment.mod.ignore_reports(), reddit_throttle_secs=1)
        return reply_comment

    def edit_content(self, content, body):
        print(f"\tEditing content {content}, body: {body}")
        self.reddit_call(lambda: content.edit(body))

    def reddit_call(self, callback, reddit_throttle_secs=5):
        if Settings.is_dry_run:
            print("\tDRY RUN!!!")
            return
        # throttle reddit calls to prevent reddit throttling
        elapsed_time = time.time() - self.last_call_time
        if elapsed_time < reddit_throttle_secs:
            time.sleep(reddit_throttle_secs - elapsed_time)
        # retry reddit exceptions, such as throttling or reddit issues
        for i in range(self.max_retries):
            try:
                result = callback()
                self.last_call_time = time.time()
                return result
            except RedditAPIException as e:
                message = f"Exception in RedditRetry: {e}\n```{traceback.format_exc()}```"
                self.discord_client.send_error_msg(message)
                print(message)
                if i < self.max_retries - 1:
                    print(f"Retrying in {self.retry_delay_secs} seconds...")
                    time.sleep(self.retry_delay_secs)
                else:
                    raise e
