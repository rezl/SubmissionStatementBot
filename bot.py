import re
import sys
import praw
import time

from datetime import datetime as dt, timedelta as td, date

# This is a file in the same folder (called config.py)
import config

# Created by /u/epicmindwarp who is amazing
#Frankenstiened by /u/LetsTalkUFOs
# 2020-04-03
RGX_SENTENCE_3 = r'(?:.{50})' # Minimum 50 characters



SUB_NAME    = 'ENTER_YOUR_SUBREDDIT_NAME'    # Set subreddit here

USER_AGENT  = f'Post Removal Bot for /r/{SUB_NAME} - v0.2'      # Info for reddit API

MINIMUM_HOURS = 1       # Number of hours a post must be

SLEEP_SECONDS = 300     # Number of seconds to sleep between scans (300 = 5 minutes)

REMOVAL_REPLY = '''
Your post has been removed for not including a submission statement. (comment on your own post). If you still wish to share your post you must resubmit your link accompanied by a submission statement of at least fifty characters.

This is a bot. Replies will not receive responses.
'''


def reddit_login():

    print('Connecting to reddit...')

    try:
        reddit = praw.Reddit(   client_id= config.client_id,
                                client_secret= config.client_secret,
                                user_agent=USER_AGENT,
                                username=config.username,
                                password=config.password)

    except Exception as e:
        print(f'\t### ERROR - Could not login.\n\t{e}')

    print(f'Logged in as: {reddit.user.me()}')
    
    return reddit



def get_latest_submissions(subreddit):

    print(f'1.1 - Getting posts  from {SUB_NAME}...')

    submissions = subreddit.new(limit=10)
    
    return submissions



def check_submissions(submissions, valid_posts):

    for submission in submissions:

        # Ignore self posts
        if submission.is_self:
            continue

        # Get the UTC unix timestamp
        ts = submission.created_utc

        # Convert to datetime format
        post_time = dt.utcfromtimestamp(ts)

        # Skip any post before today
        if post_time <= dt(2020, 5, 27, 0, 0):
            continue

        # Print a line break between each post
        print('\n')

        # Current the current UTC time
        current_time = dt.utcnow()

        # Number of whole hours (seconds / 60 / 60) between posts
        hours_since_post = int((current_time - post_time).seconds / 1800)

        print(f'{post_time} - ({hours_since_post} hrs) - {submission.title}')

        # Check if we've already marked this as valid
        if submission.id in valid_posts:
            print('\t # Already checked - valid.')

            # Go to next loop
            continue

        # Check if passed the minimum
        if hours_since_post >= MINIMUM_HOURS:

            # Once the minimum has passed
            # Create a flag, if this stays False, post to be removed
            op_left_correct_comment = False

            # Get all top level comments from the post
            for top_level_comment in submission.comments:
                
                # Look for a comment by the author
                if top_level_comment.is_submitter:

                    print('\tOP has commented')

                    # Reset the variable
                    match_found = None

                    # Grab the body
                    comment_body = top_level_comment.body

                    # Check if it matches our regex - multiline not required as it displays \n line breaks
                    match_found = re.search(RGX_SENTENCE_3, comment_body)

                    # If there is no match fiound
                    if not match_found is None:
                        
                        # Flag as correct
                        op_left_correct_comment = True

                        # Leave this loop
                        break

            # Check if the flag has changed
            if not op_left_correct_comment:
                
                print('\tOP has NOT left a valid comment!')

                # # Remove and lock the post
                submission.mod.remove()
                submission.mod.lock()

                # # Leave a comment and remove it
                removal_comment = submission.reply(REMOVAL_REPLY)
                removal_comment.mod.lock()
                removal_comment.mod.distinguish(how='yes', sticky=True)

                print('\t# Post removed.')

            else:
                # If correct, add to exceptions list
                print('\t # Post valid')
                valid_posts.append(submission.id)

    # Send back the posts we've marked as valid
    return valid_posts

############################################################################
############################################################################
############################################################################

# Bot starts here

if __name__ == "__main__":

    try:
            # Connect to reddit and return the object
            r = reddit_login()

            # Connect to the sub
            subreddit = r.subreddit(SUB_NAME)

    except Exception as e:
        print('\t\n### ERROR - Could not connect to reddit.')
        sys.exit(1)

    # A list of posts already valid, keep this in memory so we don't keep checking these
    valid_posts = []

    # Loop 4eva
    while True:

        try:
            # Get the latest submissions after emptying variable
            submissions = None
            submissions = get_latest_submissions(subreddit)
        except Exception as e:
            print('\t### ERROR - Could not get posts from reddit')

        # If there are posts, start scanning
        if not submissions is None:

            # Once you have submissions, check valid posts
            valid_posts = check_submissions(submissions, valid_posts)

        # Loop every X seconds (5 minutes)
        sleep_until = (dt.now() + td(0, SLEEP_SECONDS)).strftime('%H:%M:%S')  # Add 0 days, 300 seconds
        print(f'\nSleeping until {sleep_until}') #%Y-%m-%d 
        
        time.sleep(SLEEP_SECONDS)
