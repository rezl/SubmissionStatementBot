# Summarized:
# - moderates submission statement (recomment ss, report/remove)
# - moderates low effort flairs (removes outside casual friday)
# - reports unmoderated posts

import calendar
import config
from datetime import datetime, timedelta
import os
import praw
import time


class Settings:
    # set to True to prevent any bot actions (report, remove, comments)
    is_dry_run = False

    report_submission_statement_insufficient_length = False
    report_stale_unmoderated_posts = True
    report_submission_statement_timeout = False

    post_check_frequency_mins = 5
    post_check_threshold_mins = 2 * 60
    consecutive_old_posts = 10
    stale_post_check_frequency_mins = 60
    stale_post_check_thresholds_mins = 12 * 60

    submission_statement_pin = True
    submission_statement_time_limit_minutes = timedelta(minutes=30)
    submission_statement_minimum_char_length = 150
    submission_statement_bot_prefix = "The following submission statement was provided by"

    low_effort_flair = ["casual friday", "low effort", "humor", "humour"]
    ss_removal_reason = ("Your post has been removed for not including a submission statement, "
                         "meaning post text or a comment on your own post that provides context for the link. "
                         "If you still wish to share your post you must resubmit your link "
                         "accompanied by a submission statement of at least "
                         "" + str(submission_statement_minimum_char_length) + "characters. "
                         "\n\n"
                         "This is a bot. Replies will not receive responses. "
                         "Please message the moderators if you feel this was an error.")
    casual_hour_removal_reason = ("Your post has been removed because it was flaired as either "
                                  "Casual Friday, Humor, or Low Effort and it was not posted "
                                  "during Casual Friday. "
                                  "\n\n"
                                  "On-topic memes, jokes, short videos, image posts, posts requiring "
                                  "low effort to consume, and other less substantial posts must be "
                                  "flaired as either Casual Friday, Humor, or Low Effort, "
                                  "and they are only allowed on Casual Fridays. "
                                  "(That means 00:00 Friday – 08:00 Saturday UTC.) "
                                  "\n\n"
                                  "Clickbait, misinformation, and other similar low-quality content "
                                  "is not allowed at any time, not even on Fridays. "
                                  "\n\n"
                                  "This is a bot. Replies will not receive responses. "
                                  "Please message the moderators if you feel this was an error.")

    @staticmethod
    def submission_statement_pin_text(ss):
        header = f"{Settings.submission_statement_bot_prefix} /u/{ss.author}:\n\n---\n\n"
        footer = f"\n\n---\n\n Please reply to OP's comment here: https://old.reddit.com{ss.permalink}"
        return header + ss.body + footer


class Post:
    def __init__(self, submission):
        self.created_time = datetime.utcfromtimestamp(submission.created_utc)
        self.submission = submission
        self.submission_statement = None

    def __str__(self):
        return f"{self.submission.permalink} | {self.submission.title}"

    def has_low_effort_flair(self):
        flair = self.submission.link_flair_text
        if not flair:
            return False
        if flair.lower() in Settings.low_effort_flair:
            return True
        return False

    def submitted_during_casual_hours(self):
        # 00:00 Friday to 08:00 Saturday
        if self.created_time.isoweekday() == 5 or \
                (self.created_time.isoweekday() == 6 and self.created_time.hour < 8):
            return True
        return False

    def contains_report(self, report_substring, check_dismissed_reports):
        for report in self.submission.mod_reports:
            if any(report_substring in r for r in report):
                return True
        if check_dismissed_reports:
            # posts which haven't had dismissed reports don't contain the attr
            if hasattr(self.submission, "mod_reports_dismissed"):
                for report in self.submission.mod_reports_dismissed:
                    if report_substring in report[0]:
                        return True
        return False

    def has_bot_posted_ss(self, username):
        for comment in self.submission.comments:
            # filter removed comments to allow mods to delete current SS for bot to repost
            if (comment.author.name == username) & (not comment.removed):
                if Settings.submission_statement_bot_prefix in comment.body:
                    return True
        return False

    def contains_comment(self, text):
        for comment in self.submission.comments:
            if text in comment.body:
                return True
        return False

    def has_ss_time_expired(self):
        return self.created_time + Settings.submission_statement_time_limit_minutes < datetime.utcnow()

    def validate_submission_statement(self):
        ss_candidates = []
        for comment in self.submission.comments:
            if comment.is_submitter:
                ss_candidates.append(comment)

        if len(ss_candidates) == 0:
            return False

        # use "ss" comment, otherwise longest
        submission_statement = ""
        for candidate in ss_candidates:
            text = candidate.body.lower().strip().split()
            if ("submission" in text and "statement" in text) or ("ss" in text):
                submission_statement = candidate
                break
            if len(candidate.body) > len(submission_statement):
                submission_statement = candidate
        # print("\tsubmission statement identified from multiple comments; validated")
        self.submission_statement = submission_statement
        return True

    def is_moderator_approved(self):
        return self.submission.approved

    def is_removed(self):
        return self.submission.removed

    def report_post(self, reason):
        print(f"\tReporting post, reason: {reason}")
        if Settings.is_dry_run:
            print("\tDRY RUN!!!")
            return
        if self.contains_report(reason, True):
            print("\tPost has already been reported")
            return
        self.submission.report(reason)

    def reply_to_post(self, reason, pin=True, lock=False):
        print(f"\tReplying to post, reason: {reason}")
        if Settings.is_dry_run:
            print("\tDRY RUN!!!")
            return
        comment = self.submission.reply(reason)
        comment.mod.distinguish(sticky=pin)
        if lock:
            comment.mod.lock()

    def remove_post(self, reason, note):
        print(f"\tRemoving post, reason: {reason}")
        if Settings.is_dry_run:
            print("\tDRY RUN!!!")
            return
        self.submission.mod.remove(spam=False, mod_note=note)
        removal_comment = self.submission.reply(reason)
        removal_comment.mod.distinguish(sticky=True)


class Janitor:
    def __init__(self):
        # get config from env vars if set, otherwise from config file
        client_id = os.environ["CLIENT_ID"] if "CLIENT_ID" in os.environ else config.CLIENT_ID
        client_secret = os.environ["CLIENT_SECRET"] if "CLIENT_SECRET" in os.environ else config.CLIENT_SECRET
        bot_username = os.environ["BOT_USERNAME"] if "BOT_USERNAME" in os.environ else config.BOT_USERNAME
        bot_password = os.environ["BOT_PASSWORD"] if "BOT_PASSWORD" in os.environ else config.BOT_PASSWORD
        subreddit_name = os.environ["SUBREDDIT"] if "SUBREDDIT" in os.environ else config.SUBREDDIT
        print("CONFIG: client_id=" + client_id + " client_secret=" + "*********" +
              " bot_username=" + bot_username + " bot_password=" + "*********" +
              " subreddit_name=" + subreddit_name)

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="my user agent",
            redirect_uri="http://localhost:8080",  # unused for script applications
            username=bot_username,
            password=bot_password
        )
        self.username = bot_username
        self.subreddit = self.reddit.subreddit(subreddit_name)
        self.mod = self.subreddit.mod

        self.time_unmoderated_last_checked = datetime.utcfromtimestamp(0)

    def get_adjusted_utc_timestamp(self, time_difference_mins):
        adjusted_utc_dt = datetime.utcnow() - timedelta(minutes=time_difference_mins)
        return calendar.timegm(adjusted_utc_dt.utctimetuple())

    def fetch_new_posts(self):
        check_posts_after_utc = self.get_adjusted_utc_timestamp(Settings.post_check_threshold_mins)

        submissions = set()
        consecutive_old = 0
        # posts are provided in order of: newly submitted/approved (from automod block)
        for post in self.subreddit.new():
            if post.created_utc > check_posts_after_utc:
                submissions.add(Post(post))
                consecutive_old = 0
            # old, approved posts can show up in new amongst truly new posts due to reddit "new" ordering
            # continue checking new until consecutive_old_posts are checked, to account for these posts
            else:
                consecutive_old += 1

            if consecutive_old > Settings.consecutive_old_posts:
                return submissions
        return submissions

    def fetch_stale_unmoderated_posts(self):
        check_posts_before_utc = self.get_adjusted_utc_timestamp(Settings.stale_post_check_thresholds_mins)

        stale_unmoderated = set()
        for post in self.mod.unmoderated():
            # don't add posts which aren't old enough
            if post.created_utc < check_posts_before_utc:
                stale_unmoderated.add(Post(post))
        return stale_unmoderated

    def handle_low_effort(self, post):
        if not post.has_low_effort_flair():
            print("\tPost does not have low effort flair")
            return

        if not post.submitted_during_casual_hours():
            post.remove_post(Settings.casual_hour_removal_reason, "low effort flair")

    def handle_submission_statement(self, post):
        # TODO should we post it ahead of time if there"s a match?
        # TODO should we give a heads up (by commenting this is not done?) a few min ahead of expiration?
        # self posts don"t need a submission statement
        if post.submission.is_self:
            print("\tSelf post does not need a SS")
            return

        if post.has_bot_posted_ss(self.username):
            print("\tBot has already posted SS")
            return

        # use link post's text if valid
        if post.submission.selftext != '':
            if len(post.submission.selftext) < Settings.submission_statement_minimum_char_length:
                print("\tPost has short post-based submission statement")
                text = "Hi, thanks for your contribution. It looks like you've included your submission statement " \
                       "directly in your post, which is fine, but it is too short (min 150 chars). \n\n" \
                       "You can either edit your post's text to >150 chars, or include a comment-based ss instead " \
                       "(which I would post shortly, if it meets submission statement requirements).\n" \
                       "Responses to this comment are not monitored."
                if not post.contains_comment(text):
                    post.reply_to_post(text, pin=False, lock=True)
            else:
                print("\tPost has valid post-based submission statement, not doing anything")
                return

        # users are given time to post a submission statement
        if not post.has_ss_time_expired():
            print("\tTime has not expired")
            return

        print("\tTime has expired")
        # TODO probably should verify ss length in this validate method
        if post.validate_submission_statement():
            if not post.submission_statement:
                reason = "ERROR: no submission statement found, please check and report to devs"
                post.report_post(reason)
                print(reason)
                raise Exception("invalid state: no submission statement found, but reported as valid")
            print("\tPost has submission statement")
            if Settings.submission_statement_pin:
                post.reply_to_post(Settings.submission_statement_pin_text(post.submission_statement),
                                   pin=True, lock=True)

            # verify submission statements have at least required length, report if necessary
            if len(post.submission_statement.body) < Settings.submission_statement_minimum_char_length:
                reason = "Submission statement is too short"
                if Settings.report_submission_statement_insufficient_length:
                    post.report_post(reason)
                else:
                    post.remove_post(Settings.ss_removal_reason, reason)
        else:
            print("\tPost does NOT have submission statement")

            if post.is_moderator_approved():
                reason = "Moderator approved post, but there is no SS. Please double check."
                post.report_post(reason)
            elif Settings.report_submission_statement_timeout:
                reason = "Post has no submission statement after timeout. Please take a look."
                post.report_post(reason)
            else:
                post.remove_post(Settings.ss_removal_reason, "No submission statement")

    def handle_posts(self):
        print(f"Checking posts")
        posts = self.fetch_new_posts()
        for post in posts:
            print(f"Checking post: {post.submission.title}\n\t{post.submission.permalink}")

            if post.submission.removed:
                print("\tERROR: post has been removed but is in submissions?")
                continue

            try:
                self.handle_low_effort(post)
                self.handle_submission_statement(post)
            except Exception as e:
                print(e)

    def handle_stale_unmoderated_posts(self):
        now = datetime.utcnow()
        if self.time_unmoderated_last_checked > now - timedelta(minutes=Settings.stale_post_check_frequency_mins):
            return

        stale_unmoderated_posts = self.fetch_stale_unmoderated_posts()
        print("__UNMODERATED__")
        for post in stale_unmoderated_posts:
            print(f"Checking unmoderated post: {post.submission.title}")
            if Settings.report_stale_unmoderated_posts:
                reason = "This post is over " + str(round(Settings.stale_post_check_thresholds_mins / 60, 2)) + \
                         "hours old and has not been moderated. Please take a look!"
                post.report_post(reason)
            else:
                print(f"Not reporting stale unmoderated post: {post.submission.title}\n\t{post.submission.permalink}")
        self.time_unmoderated_last_checked = now


def run_forever():
    while True:
        try:
            janitor = Janitor()
            while True:
                print("____________________")
                janitor.handle_posts()
                janitor.handle_stale_unmoderated_posts()
                time.sleep(Settings.post_check_frequency_mins * 60)
        except Exception as e:
            print(e)
        time.sleep(Settings.post_check_frequency_mins * 60)


def run_once():
    janitor = Janitor()
    janitor.handle_posts()
    janitor.handle_stale_unmoderated_posts()


if __name__ == "__main__":
    # run_once()
    run_forever()
