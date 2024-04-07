import calendar
import traceback
from threading import Thread

import config
from datetime import datetime, timedelta
from enum import Enum
import os
import praw

from discord_client import DiscordClient
from reddit_actions_handler import RedditActionsHandler
from settings import *
import time

from subreddit_tracker import SubredditTracker


class Post:
    def __init__(self, submission):
        self.submission = submission
        self.created_time = datetime.utcfromtimestamp(submission.created_utc)

    def __str__(self):
        return f"{self.submission.permalink} | {self.submission.title}"

    def has_low_effort_flair(self, settings):
        flair = self.submission.link_flair_text
        if not flair:
            return False
        if flair.lower() in settings.low_effort_flair:
            return True
        return False

    def submitted_during_casual_hours(self):
        # 00:00 Friday to 08:00 Saturday
        if self.created_time.isoweekday() == 5 or \
                (self.created_time.isoweekday() == 6 and self.created_time.hour < 8):
            return True
        return False

    def find_comment_containing(self, text, include_deleted=False):
        for comment in self.submission.comments:
            if not include_deleted:
                if isinstance(comment.author, type(None)) or comment.removed:
                    continue

            if text in comment.body:
                return comment
        return None

    def is_post_old(self, time_mins):
        return self.created_time + timedelta(minutes=time_mins) < datetime.utcnow()

    def find_submission_statement(self):
        ss_candidates = []
        for comment in self.submission.comments:
            if comment.is_submitter:
                ss_candidates.append(comment)

        if len(ss_candidates) == 0:
            return None

        # use "ss" comment, otherwise longest
        submission_statement = ss_candidates[0]
        for candidate in ss_candidates:
            text = candidate.body.lower()
            if ("submission statement" in text) or (" ss " in text):
                return candidate
            if len(candidate.body) > len(submission_statement.body):
                submission_statement = candidate
        return submission_statement

    def is_moderator_approved(self):
        return self.submission.approved

    def is_removed(self):
        return self.submission.removed


class SubmissionStatementState(str, Enum):
    MISSING = "MISSING"
    TOO_SHORT = "TOO_SHORT"
    VALID = "VALID"


class Janitor:
    def __init__(self, discord_client, bot_username, reddit, reddit_handler):
        self.discord_client = discord_client
        self.bot_username = bot_username
        self.reddit = reddit
        self.reddit_handler = reddit_handler

    @staticmethod
    def get_adjusted_utc_timestamp(time_difference_mins):
        adjusted_utc_dt = datetime.utcnow() - timedelta(minutes=time_difference_mins)
        return calendar.timegm(adjusted_utc_dt.utctimetuple())

    def fetch_new_posts(self, settings, subreddit):
        check_posts_after_utc = self.get_adjusted_utc_timestamp(settings.post_check_threshold_mins)

        submissions = list()
        consecutive_old = 0
        # posts are provided in order of: newly submitted/approved (from automod block)
        for post in subreddit.new():
            if post.created_utc > check_posts_after_utc:
                submissions.append(Post(post))
                consecutive_old = 0
            # old, approved posts can show up in new amongst truly new posts due to reddit "new" ordering
            # continue checking new until consecutive_old_posts are checked, to account for these posts
            else:
                submissions.append(Post(post))
                consecutive_old += 1

            if consecutive_old > settings.consecutive_old_posts:
                return submissions
        return submissions

    def fetch_stale_unmoderated_posts(self, settings, subreddit_mod):
        check_posts_before_utc = self.get_adjusted_utc_timestamp(settings.stale_post_check_threshold_mins)

        stale_unmoderated = list()
        for post in subreddit_mod.unmoderated():
            # don't add posts which aren't old enough
            if post.created_utc < check_posts_before_utc:
                stale_unmoderated.append(Post(post))
        return stale_unmoderated

    @staticmethod
    def validate_submission_statement(settings, ss):
        if ss is None:
            return SubmissionStatementState.MISSING
        elif len(ss.body) < settings.submission_statement_minimum_char_length:
            return SubmissionStatementState.TOO_SHORT
        else:
            return SubmissionStatementState.VALID

    def handle_low_effort(self, settings, post):
        if post.submission.approved:
            return

        if not post.has_low_effort_flair(settings):
            return

        if not post.submitted_during_casual_hours():
            self.reddit_handler.remove_content(post.submission, settings.casual_hour_removal_reason,
                                               "low effort flair")

    def handle_submission_statement(self, subreddit_tracker, post, ss_prefix):
        settings = subreddit_tracker.settings
        # self posts don't need a submission statement
        if post.submission.is_self:
            print("\tSelf post does not need a SS")
            if ss_prefix and not post.find_comment_containing(ss_prefix):
                print("\tSelf post needs prefix comment, adding")
                self.reddit_handler.reply_to_content(post.submission, ss_prefix, pin=True, lock=True)
            return

        bot_ss_comment = post.find_comment_containing(settings.submission_statement_bot_prefix)
        if bot_ss_comment:
            print("\tBot has already posted SS")
            if settings.submission_statement_edit_support:
                try:
                    bot_ss_comment_split = bot_ss_comment.body.split("/")
                    actual_ss_id = bot_ss_comment_split[len(bot_ss_comment_split) - 2]
                    actual_ss = self.reddit.comment(id=actual_ss_id)
                    # original ss is edited if not in bot comment --> should edit
                    if actual_ss.body not in bot_ss_comment.body and bot_ss_comment.author.name == "StatementBot":
                        print("\tActual ss has been edited. Editing bot ss")
                        submission_statement_content = settings.submission_statement_pin_text(actual_ss, ss_prefix)
                        self.reddit_handler.edit_content(bot_ss_comment, submission_statement_content)
                except Exception as e:
                    message = f"Exception in identifying ss edits, won't edit." \
                              f" {post.submission.title}: {e}\n```{traceback.format_exc()}```"
                    self.discord_client.send_error_msg(message)
                    print(message)
            return

        ss_optional = False
        # use link post's text if valid
        if post.submission.selftext != '':
            if len(post.submission.selftext) < settings.submission_statement_minimum_char_length:
                print("\tPost has short post-based submission statement")
                text = "Hi, thanks for your contribution. It looks like you've included your submission statement " \
                       "directly in your post, which is fine, but it is too short (min 150 chars). \n\n" \
                       "You can either edit your post's text to >150 chars, or include a comment-based ss instead " \
                       "(which I would post shortly, if it meets submission statement requirements).\n" \
                       "Please message the moderators if you feel this was an error. " \
                       "Responses to this comment are not monitored."
                if not post.find_comment_containing(text, include_deleted=True):
                    self.reddit_handler.reply_to_content(post.submission, text, pin=False, lock=True)
            else:
                print("\tPost has valid post-based submission statement, a comment based ss is optional")
                ss_optional = True

        submission_statement = post.find_submission_statement()
        submission_statement_state = Janitor.validate_submission_statement(settings, submission_statement)

        timeout_mins = settings.submission_statement_time_limit_mins
        reminder_mins = timeout_mins / 2

        if not ss_optional:
            self.ss_on_topic_check(subreddit_tracker.monitored_ss_replies, settings, post,
                                   submission_statement, submission_statement_state, timeout_mins)
            self.ss_final_reminder(settings, post, submission_statement, submission_statement_state,
                                   reminder_mins, timeout_mins)

        # users are given time to post a submission statement
        if not post.is_post_old(timeout_mins):
            print("\tTime has not expired")
            return
        print("\tTime has expired")

        self.remove_bot_comments(post)

        if submission_statement_state == SubmissionStatementState.MISSING:
            print("\tPost does NOT have submission statement")
            if not ss_optional:
                if post.is_moderator_approved():
                    self.reddit_handler.report_content(post.submission,
                                                       "Moderator approved post, but there is no SS. Please look.")
                elif settings.report_submission_statement_timeout:
                    self.reddit_handler.report_content(post.submission,
                                                       "Post has no submission statement after timeout. Please look.")
                else:
                    self.reddit_handler.remove_content(post.submission, settings.ss_removal_reason,
                                                       "No submission statement")
        elif submission_statement_state == SubmissionStatementState.TOO_SHORT:
            print("\tPost has too short submission statement")
            if ss_optional:
                if settings.submission_statement_pin:
                    submission_statement_content = settings.submission_statement_pin_text(submission_statement, ss_prefix)
                    self.reddit_handler.reply_to_content(post.submission, submission_statement_content,
                                                         pin=True, lock=True)
            else:
                if settings.submission_statement_pin:
                    submission_statement_content = settings.submission_statement_pin_text(submission_statement, ss_prefix)
                    self.reddit_handler.reply_to_content(post.submission,
                                                         submission_statement_content,
                                                         pin=True, lock=True)
                if post.is_moderator_approved():
                    reason = "Moderator approved post, but SS is too short. Please double check."
                    self.reddit_handler.report_content(post.submission, reason)
                elif settings.report_submission_statement_insufficient_length:
                    self.reddit_handler.report_content(post.submission, "Submission statement is too short")
                else:
                    reason = "Submission statement is too short"
                    self.reddit_handler.remove_content(post.submission, settings.ss_removal_reason, reason)
        elif submission_statement_state == SubmissionStatementState.VALID:
            print("\tPost has valid submission statement")
            if settings.submission_statement_pin:
                submission_statement_content = settings.submission_statement_pin_text(submission_statement, ss_prefix)
                self.reddit_handler.reply_to_content(post.submission, submission_statement_content,
                                                     pin=True, lock=True)
        else:
            raise RuntimeError(f"\tUnsupported submission_statement_state: {submission_statement_state}")

    def ss_on_topic_check(self, monitored_ss_replies, settings, post, submission_statement, submission_statement_state,
                          timeout_mins):
        # not enabled, or malformed (enabled, but missing keywords or response)
        if not settings.submission_statement_on_topic_reminder or \
                not settings.submission_statement_on_topic_keywords or \
                not settings.submission_statement_on_topic_response:
            return
        if post.is_post_old(timeout_mins):
            return
        if submission_statement_state == SubmissionStatementState.MISSING:
            return

        response_keyword = settings.submission_statement_on_topic_response
        on_topic_identifier = f"Does this submission statement explain how your post is related to {response_keyword}?"
        bot_comment = None
        for reply in submission_statement.replies:
            if on_topic_identifier in reply.body:
                bot_comment = reply
                break

        text = submission_statement.body.lower()
        contains_on_topic_keyword = False
        for keyword in settings.submission_statement_on_topic_keywords:
            if keyword in text:
                contains_on_topic_keyword = True
                break

        # remove bot comment if post is approved or has been edited to contain a keyword
        if post.submission.approved:
            self.remove_on_topic(monitored_ss_replies, bot_comment,
                                 "Removed ss reply due to approved post")
            return
        elif contains_on_topic_keyword:
            self.remove_on_topic(monitored_ss_replies, bot_comment,
                                 "Removed ss reply due to edited ss contains keyword")
            return
        elif bot_comment and bot_comment.score < settings.submission_statement_on_topic_removal_score:
            self.remove_on_topic(monitored_ss_replies, bot_comment,
                                 f"Removed ss reply due to low score: {str(bot_comment.score)}")
            return
        elif bot_comment and bot_comment.score > settings.submission_statement_on_topic_report_score:
            reason = f"Bot on-topic comment upvoted too much: " \
                     f"Check post is related to collapse and ss is good"
            self.reddit_handler.report_content(bot_comment, reason)

        # bot comment exists, or ss is already on topic
        if bot_comment or contains_on_topic_keyword:
            return

        response = f"{on_topic_identifier}\n\n" \
                   f"* If it does, downvote this comment\n\n" \
                   f"* If it doesn't, please edit to include that\n\n" \
                   f"Keeping content on-topic is important to our community, and submission statements help achieve " \
                   f"that. Thanks for your submission!"
        comment = self.reddit_handler.reply_to_content(submission_statement, response,
                                                       pin=False, lock=True, ignore_reports=True)
        if comment is not None and settings.submission_statement_on_topic_check_downvotes:
            monitored_ss_replies.append(comment.id)

    def ss_final_reminder(self, settings, post, submission_statement, submission_statement_state,
                          reminder_timeout_mins, timeout_mins):
        if not settings.submission_statement_final_reminder:
            return
        # only applies to posts that are between the time to remind and time to post
        if not post.is_post_old(reminder_timeout_mins) or post.is_post_old(timeout_mins):
            return
        if submission_statement_state == SubmissionStatementState.VALID:
            return
        reminder_identifier = "As a final reminder, your post must include a valid submission statement"
        if post.find_comment_containing(reminder_identifier):
            return

        # one final reminder to post a ss
        reminder_detail = "Your post is missing a submission statement." \
            if submission_statement_state == SubmissionStatementState.MISSING \
            else f"The submission statement I identified is too short ({len(submission_statement.body)}" \
                 f" chars):\n> {submission_statement.body} \n\n" \
                 f"https://old.reddit.com{submission_statement.permalink}"
        reminder_response = f"{reminder_identifier} within {timeout_mins} min. {reminder_detail}\n\n" \
                            f"{settings.submission_statement_rule_description}.\n\n" \
                            "Please message the moderators if you feel this was an error. " \
                            "Responses to this comment are not monitored."
        self.reddit_handler.reply_to_content(post.submission, reminder_response, pin=False, lock=True)

    def handle_posts(self, subreddit_tracker):
        settings = subreddit_tracker.settings
        subreddit = subreddit_tracker.subreddit
        posts = self.fetch_new_posts(settings, subreddit)
        print("Checking " + str(len(posts)) + " posts")
        for post in posts:
            print(f"Checking post: {post.submission.title}\n\t{post.submission.permalink}")

            try:
                self.handle_low_effort(settings, post)
                prefix = settings.flair_pin_text(post.submission.link_flair_text)
                self.handle_submission_statement(subreddit_tracker, post, prefix)
            except Exception as e:
                message = f"Exception when handling post {post.submission.title}: {e}\n```{traceback.format_exc()}```"
                self.discord_client.send_error_msg(message)
                print(message)

    def handle_stale_unmoderated_posts(self, subreddit_tracker):
        now = datetime.utcnow()
        settings = subreddit_tracker.settings
        subreddit_mod = subreddit_tracker.subreddit.mod
        last_checked = subreddit_tracker.time_unmoderated_last_checked
        if last_checked > now - timedelta(minutes=settings.stale_post_check_frequency_mins):
            return

        stale_unmoderated_posts = self.fetch_stale_unmoderated_posts(settings, subreddit_mod)
        print("__UNMODERATED__")
        for post in stale_unmoderated_posts:
            print(f"Checking unmoderated post: {post.submission.title}")
            if settings.report_stale_unmoderated_posts:
                rounded_time = str(round(settings.stale_post_check_threshold_mins / 60, 2))
                reason = f"This post is over {rounded_time} hours old and has not been moderated. Please take a look!"
                self.reddit_handler.report_content(post.submission, reason)
            else:
                print(f"Not reporting stale unmoderated post: {post.submission.title}\n\t{post.submission.permalink}")
        subreddit_tracker.time_unmoderated_last_checked = now

    def handle_monitored_ss_replies(self, subreddit_tracker):
        settings = subreddit_tracker.settings
        if not settings.submission_statement_on_topic_check_downvotes:
            return

        print(f"Monitored ss replies: {str(list(subreddit_tracker.monitored_ss_replies))}")
        removal_score = settings.submission_statement_on_topic_removal_score
        for comment_id in list(subreddit_tracker.monitored_ss_replies):
            comment = self.reddit.comment(id=comment_id)
            # deleted/removed comment or post
            if comment is None or isinstance(comment.author, type(None)) or comment.removed \
                    or isinstance(comment.submission.author, type(None)) or comment.submission.removed:
                print(f"Not monitoring {comment_id} anymore, comment or post is removed/deleted")
                subreddit_tracker.monitored_ss_replies.remove(comment_id)
            elif comment.score < removal_score:
                self.remove_on_topic(subreddit_tracker.monitored_ss_replies, comment,
                                     f"Removed {comment_id} due to low score: {str(comment.score)}")
            elif comment.submission.approved:
                self.remove_on_topic(subreddit_tracker.monitored_ss_replies, comment,
                                     f"Removed {comment_id} due to approved post")
            elif comment.created_utc < self.get_adjusted_utc_timestamp(60 * 24):
                print(f"Not monitoring {comment_id} anymore, over 1 day old and has [{str(comment.score)}] score")
                subreddit_tracker.monitored_ss_replies.remove(comment_id)

    def remove_bot_comments(self, post):
        for comment in post.submission.comments:
            # deleted comment
            if isinstance(comment.author, type(None)) or comment.removed:
                continue
            if comment.author == self.bot_username:
                removal_reason = "Cleaned up non-submission statement comment"
                self.reddit_handler.remove_content(comment, removal_reason, removal_reason, reply=False)

    def remove_on_topic(self, monitored_ss_replies, bot_comment, reason):
        if bot_comment in monitored_ss_replies:
            self.reddit_handler.remove_content(bot_comment, reason, reason, reply=False)
            monitored_ss_replies.remove(bot_comment.id)


if __name__ == "__main__":
    # get config from env vars if set, otherwise from config file
    client_id = os.environ.get("CLIENT_ID", config.CLIENT_ID)
    client_secret = os.environ.get("CLIENT_SECRET", config.CLIENT_SECRET)
    bot_username = os.environ.get("BOT_USERNAME", config.BOT_USERNAME)
    bot_password = os.environ.get("BOT_PASSWORD", config.BOT_PASSWORD)
    discord_token = os.environ.get("DISCORD_TOKEN", config.DISCORD_TOKEN)
    discord_error_guild_name = os.environ.get("DISCORD_ERROR_GUILD", config.DISCORD_ERROR_GUILD)
    discord_error_channel_name = os.environ.get("DISCORD_ERROR_CHANNEL", config.DISCORD_ERROR_CHANNEL)
    subreddits_config = os.environ.get("SUBREDDITS", config.SUBREDDITS)
    subreddit_names = [subreddit.strip() for subreddit in subreddits_config.split(",")]
    print("CONFIG: subreddit_names=" + str(subreddit_names) + ", client_id=" + client_id)

    discord_client = DiscordClient(discord_error_guild_name, discord_error_channel_name)
    discord_client.add_commands()
    Thread(target=discord_client.run, args=(discord_token,)).start()

    while not discord_client.is_ready:
        time.sleep(1)

    while True:
        try:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent="flyio:com.statementbot.statement-bot:v3.1",
                redirect_uri="http://localhost:8080",  # unused for script applications
                username=bot_username,
                password=bot_password
            )

            reddit_handler = RedditActionsHandler(reddit, discord_client)

            subreddit_trackers = list()
            for subreddit_name in subreddit_names:
                settings = SettingsFactory.get_settings(subreddit_name)
                print(f"Creating Subreddit: {subreddit_name} with {type(settings).__name__} settings")
                subreddit = reddit.subreddit(subreddit_name)
                subreddit_tracker = SubredditTracker(subreddit, settings)
                subreddit_trackers.append(subreddit_tracker)

            janitor = Janitor(discord_client, bot_username, reddit, reddit_handler)
            while True:
                for subreddit_tracker in subreddit_trackers:
                    try:
                        print("____________________")
                        print(f"Checking Subreddit: {subreddit_tracker.subreddit_name}")
                        janitor.handle_posts(subreddit_tracker)
                        janitor.handle_stale_unmoderated_posts(subreddit_tracker)
                        janitor.handle_monitored_ss_replies(subreddit_tracker)
                    except Exception as e:
                        message = f"Exception when handling all posts: {e}\n```{traceback.format_exc()}```"
                        discord_client.send_error_msg(message)
                        print(message)
                time.sleep(Settings.post_check_frequency_mins * 60)
        except Exception as e:
            message = f"Exception in main processing: {e}\n```{traceback.format_exc()}```"
            discord_client.send_error_msg(message)
            print(message)
            time.sleep(Settings.post_check_frequency_mins * 60)

