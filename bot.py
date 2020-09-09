import re
import sys
import time
import traceback
from datetime import datetime, timedelta
from typing import List, Set, NoReturn

import praw

# This is a file in the same folder (called config.py)
import config

# Created by /u/epicmindwarp who is amazing
# Frankenstiened by /u/LetsTalkUFOs
# Further modified by /u/iPlain
# 2020-09-03

SUB_NAME = 'ENTER_YOUR_SUBREDDIT_NAME'  # Set subreddit here

USER_AGENT = f'Post Removal Bot for /r/{SUB_NAME} - v0.3'  # Info for reddit API

SLEEP_SECONDS = 300  # Number of seconds to sleep between scans (300 = 5 minutes)

MEME_FLAIR_NAME = 'MEME'

MEME_REMOVAL_REPLY = '''Your post has been removed as Meme posts are only allowed on Meme Mondays.

This is a bot. Replies will not receive responses.
'''


class BadPostError(Exception):
    def __init__(self, log_message, user_message):
        self.log_message = log_message
        self.user_message = user_message


def reddit_login() -> praw.reddit.Reddit:
    print('Connecting to reddit...')
    reddit = praw.Reddit(client_id=config.client_id,
                         client_secret=config.client_secret,
                         user_agent=USER_AGENT,
                         username=config.username,
                         password=config.password)
    print(f'Logged in as: {reddit.user.me()}')
    return reddit


def is_monday_in_usa(utc_time: datetime) -> bool:
    """Checks if a datetime is Monday in UTC+4"""
    offset_time = utc_time + timedelta(hours=-4)
    return offset_time.date().isoweekday() == 1


def check_submission_for_meme_monday(submission: praw.reddit.Submission) -> bool:
    """
    Check if the submission is a meme post outside the given time frame.
    :param submission: The PRAW Submission to check.
    :return: True if the post is valid. False if the post is not validated but should not be removed.
    :raises: BadPostError if the post should be removed.
    """
    if submission.link_flair_text is None:
        # If there is no flair, don't remove, but check later.
        return False
    if submission.link_flair_text != MEME_FLAIR_NAME:
        return True

    post_time = datetime.utcfromtimestamp(submission.created_utc)
    if is_monday_in_usa(post_time):
        return True
    raise BadPostError('Meme post not on a Monday!', MEME_REMOVAL_REPLY)


def check_submissions(submissions: List[praw.reddit.Submission], valid_submission_ids: Set[str]) -> None:
    """
    Check the list of submissions and remove them if they break the rules.
    :param submissions: A list of PRAW Submission objects.
    :param valid_submission_ids: A set of Reddit submission IDs.
    :return: None.
    """
    for submission in submissions:
        if submission.id in valid_submission_ids or submission.distinguished:
            continue
        print(f"Submission: {submission.title}, {submission.permalink}")
        try:
            meme_monday_valid = check_submission_for_meme_monday(submission)
            if meme_monday_valid:
                print("Valid submission")
                valid_submission_ids.add(submission.id)
            else:
                print(f"Doesn't yet have a flair, so won't remove, but will check back later.")
        except BadPostError as e:
            print(e.log_message)
            submission.mod.remove()
            submission.mod.lock()
            removal_comment = submission.reply(e.user_message)
            removal_comment.mod.lock()
            removal_comment.mod.distinguish(sticky=True)
            print('Post removed.')


def main() -> NoReturn:
    try:
        reddit = reddit_login()
        subreddit = reddit.subreddit(SUB_NAME)
    except Exception as e:
        print(f'### ERROR - Could not connect to Reddit.\n{e}')
        sys.exit(1)

    # A list of posts already valid, keep this in memory so we don't keep checking these
    valid_posts = set()

    # Loop 4eva
    while True:
        try:
            # Get the latest submissions after emptying variable
            print('')
            print(f'Getting posts from {SUB_NAME}...')
            submissions = subreddit.new()
            print('Checking submissions...')
            check_submissions(submissions, valid_posts)
        except Exception as e:
            print(f'### ERROR - Could not get posts from reddit.\n{e}')
            traceback.print_exc()

        print(f'Sleeping for {SLEEP_SECONDS} seconds')
        time.sleep(SLEEP_SECONDS)


if __name__ == '__main__':
    main()
