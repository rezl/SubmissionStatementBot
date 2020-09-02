import re
import sys
import praw
import time
import traceback

from datetime import datetime as dt, timedelta

# This is a file in the same folder (called config.py)
import config

# Created by /u/epicmindwarp who is amazing
# Frankenstiened by /u/LetsTalkUFOs
# Further modified by /u/iPlain
# 2020-09-03
RGX_SENTENCE_3 = r'(?:.{50})'  # Minimum 50 characters

SUB_NAME = 'ENTER_YOUR_SUBREDDIT_NAME'  # Set subreddit here

USER_AGENT = f'Post Removal Bot for /r/{SUB_NAME} - v0.3'  # Info for reddit API

MINIMUM_HOURS_FOR_SUBMISSION_STATEMENT = 1  # Number of hours a post must be

SLEEP_SECONDS = 300  # Number of seconds to sleep between scans (300 = 5 minutes)

LOW_EFFORT_FLAIR_NAME = 'Low Effort'

SUBMISSION_STATEMENT_REMOVAL_REPLY = '''Your post has been removed for not including a submission statement. (comment 
on your own post). If you still wish to share your post you must resubmit your link accompanied by a submission 
statement of at least fifty characters. 

This is a bot. Replies will not receive responses.
'''

LOW_EFFORT_REMOVAL_REPLY = '''Your post has been removed as Low Effort posts are only allowed on Shitpost 
Fridays. 

This is a bot. Replies will not receive responses.
'''


class BadPostError(Exception):
    def __init__(self, log_message, user_message):
        self.log_message = log_message
        self.user_message = user_message


def reddit_login():
    print('Connecting to reddit...')
    reddit = praw.Reddit(client_id=config.client_id,
                         client_secret=config.client_secret,
                         user_agent=USER_AGENT,
                         username=config.username,
                         password=config.password)
    print(f'Logged in as: {reddit.user.me()}')
    return reddit


def is_friday_in_usa(utc_time):
    """Checks if a datetime is Friday in UTC+4"""
    offset_time = utc_time + timedelta(hours=-4)
    print(f"Time check: {utc_time}, {offset_time}, {offset_time.date().isoweekday()}")
    return offset_time.date().isoweekday() == 5


def check_submission_for_submission_statement(submission):
    """
    Check if the submission has a valid submission statement.
    :param submission: The PRAW Submission to check.
    :return: True if the post is valid. False if the post is not validated but should not be removed.
    :raises: BadPostError if the post should be removed.
    """
    if submission.is_self:
        return True
    post_time = dt.utcfromtimestamp(submission.created_utc)
    current_time = dt.utcnow()

    # Number of whole hours (seconds / 60 / 60) between posts
    hours_since_post = int((current_time - post_time).seconds / 1800)

    if hours_since_post < MINIMUM_HOURS_FOR_SUBMISSION_STATEMENT:
        # If it hasn't been long enough, don't remove, but check later.
        return False
    for top_level_comment in submission.comments:
        if top_level_comment.is_submitter:
            if re.match(RGX_SENTENCE_3, top_level_comment.body):
                return True
    # No valid comment from OP
    raise BadPostError('Op has NOT left a valid comment!', SUBMISSION_STATEMENT_REMOVAL_REPLY)


def check_submission_for_low_effort(submission):
    """
    Check if the submission is a low effort post outside the given time frame.
    :param submission: The PRAW Submission to check.
    :return: True if the post is valid. False if the post is not validated but should not be removed.
    :raises: BadPostError if the post should be removed.
    """
    if submission.link_flair_text is None:
        # If there is no flair, don't remove, but check later.
        return False
    if submission.link_flair_text != LOW_EFFORT_FLAIR_NAME:
        return True

    post_time = dt.utcfromtimestamp(submission.created_utc)
    if is_friday_in_usa(post_time):
        return True
    raise BadPostError('Low Effort post not on a Friday!', LOW_EFFORT_REMOVAL_REPLY)


def check_submissions(submissions, valid_submission_ids):
    """
    Check the list of submissions and remove them if they break the rules.
    :param submissions: A list of PRAW Submission objects.
    :param valid_submission_ids: A set of Reddit submission IDs.
    :return: None.
    """
    for submission in submissions:
        if submission.id in valid_submission_ids:
            continue
        print(f"Submission: {submission.title}, {submission.url}")
        try:
            low_effort_valid = check_submission_for_low_effort(submission)
            sub_statement_valid = check_submission_for_submission_statement(submission)
            if low_effort_valid and sub_statement_valid:
                print("Valid submission")
                valid_submission_ids.add(submission.id)
            else:
                print(f"Something not yet valid but not remove worthy: Low effort valid: {low_effort_valid}, "
                      f"Submission statement valid: {sub_statement_valid}")
        except BadPostError as e:
            print(e.log_message)
            submission.mod.remove()
            submission.mod.lock()
            removal_comment = submission.reply(e.user_message)
            removal_comment.mod.lock()
            removal_comment.mod.distinguish(sticky=True)
            print('Post removed.')


def main():
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
