# Goals:
# - check if post has submission statement
#   - configure whether you remove or report if there is no ss
#   - configure whether you remove or report if ss is not of sufficient length
# - corner cases:
#   - moderator already commented
#   - moderator already approved
#   -
# Goals:
# - only allow certain flairs on certain days of the week
# - (e.g. casual friday)
#
#
# Constraints:
# - only check last 24 hours
#   - avoid going back in time too far
#   - remember which posts were approved
#   - probably want to pickle these, keep a sliding window
# - avoid rechecking the same posts repeatedly
# - recover if Reddit is down
# - want bot to be easily configurable
# - want a debug mode, so that collapsebot doesn't confuse people

import calendar
import config
from datetime import datetime, timedelta
import praw
import time


###############################################################################
###
### Helper class -- settings base class
###
###############################################################################

class SubredditSettings:
    def __init__(self):
        # list of flair text, in lower case
        self.low_effort_flair = []
        self.removal_reason = "Your post has been removed"
        self.casual_hour_removal_reason = "Your post has been removed"
        self.submission_statement_time_limit_minutes = timedelta(hours=0, minutes=30)
        self.submission_statement_minimum_char_length = 150
        self.report_insufficient_length = False
        self.report_old_posts = False
        self.pin_submission_statement = False

    def post_has_low_effort_flair(self, post):
        flair = post._submission.link_flair_text
        if not flair:
            return False
        if flair.lower() in self.low_effort_flair:
            return True
        return False

    def submitted_during_casual_hours(self, post):
        return False

    def removal_text(self):
        return self.removal_reason

    def casual_removal_text(self):
        return self.casual_hour_removal_reason

    def submission_statement_pin_text(self, ss):
        # construct a message to pin, by quoting OP's submission statement
        # submission_statement is a top level comment
        header = f"The following submission statement was provided by /u/{ss.author}:\n\n---\n\n"
        footer = f"\n\n---\n\n Please reply to OP's comment here: https://old.reddit.com{ss.permalink}"
        return header + ss.body + footer


###############################################################################
###
### Helper class -- settings for /r/Futurology
###
###############################################################################

class FuturologySettings(SubredditSettings):
    def __init__(self):
        super().__init__()
        self.removal_reason = "We require that posters seed their post with an initial comment, a Submission Statement, that suggests a line of future-focused discussion for the topic posted. We want this submission statement to elaborate on the topic being posted and suggest how it might be discussed in relation to the future, and ask that it is a minimum of 300 characters. Could you please repost with a Submission Statement, thanks."
        self.submission_statement_minimum_char_length = 300
        self.report_insufficient_length = True
        self.pin_submission_statement = True

    def submission_statement_pin_text(self, ss):
        # construct a message to pin, by quoting OP's submission statement
        # ss is a top level comment, the submission statement

        verbiage = f"The following submission statement was provided by /u/{ss.author}:\n\n---\n\n"
        verbiage = verbiage + ss.body
        verbiage = verbiage + f"\n\n---\n\n Please reply to OP's comment here: https://old.reddit.com{ss.permalink}"
        return verbiage


###############################################################################
###
### Helper class -- settings for /r/Collapse
###
###############################################################################

class CollapseSettings(SubredditSettings):
    def __init__(self):
        # lower case
        super().__init__()
        self.low_effort_flair = ['casual friday', 'low effort', 'humor', 'humour']
        self.removal_reason = ("Your post has been removed for not including a submission statement, "
                               "meaning a comment on your own post that provides context for the link. "
                               "If you still wish to share your post you must resubmit your link "
                               "accompanied by a submission statement of at least one hundred fifty characters. "
                               "\n\n"
                               "This is a bot. Replies will not receive responses.")

        self.casual_hour_removal_reason = ('Your post in r/collapse was removed because it was flaired as either '
                                           '"Casual Friday", "Humor", or "Low Effort" and it was not posted '
                                           'during Casual Friday. '
                                           "\n\n"
                                           'On-topic memes, jokes, short videos, image posts, posts requiring '
                                           'low effort to consume, and other less substantial posts must be '
                                           'flaired as either "Casual Friday", "Humor", or "Low Effort", '
                                           'and they are only allowed on Casual Fridays. '
                                           '(That means 00:00 Friday – 08:00 Saturday UTC.) '
                                           "\n\n"
                                           'Clickbait, misinformation, and other similar low-quality content '
                                           'is not allowed at any time, not even on Fridays. '
                                           "\n\n"
                                           'This is a bot. Replies will not receive responses. '
                                           'Please [message the moderators](https://www.reddit.com/message/compose?to=%2Fr%2Fcollapse&subject=Friday%20Removal) '
                                           'if you feel this was an error.')

        self.submission_statement_minimum_char_length = 150
        self.report_old_posts = True
        self.pin_submission_statement = True

    def submitted_during_casual_hours(self, post):
        posted_on_friday = False
        timestamp = post._submission.created_utc
        timestamp = datetime.utcfromtimestamp(timestamp)

        # 08:00 Friday to 00:00 Saturday
        if timestamp.isoweekday() == 5 or (timestamp.isoweekday() == 6 and timestamp.hour < 8):
            posted_on_friday = True

        return posted_on_friday


###############################################################################
###
### Helper class -- wrapper for PRAW submissions
###
###############################################################################

class Post:
    def __init__(self, submission, time_limit=30):
        self._submission = submission
        self._created_time = datetime.utcfromtimestamp(submission.created_utc)
        self._submission_statement_validated = False
        self._submission_statement = None
        self._is_text_post = False
        self._post_was_serviced = False
        if submission.is_self:
            self._is_text_post = True
            self._post_was_serviced = True
        self._time_limit = time_limit

        # debugging
        # print(submission.title)
        # print("TIME EXPIRED?")
        # print(self.has_time_expired())

    def __eq__(self, other):
        return self._submission.permalink == other._submission.permalink

    def __hash__(self):
        return hash(self._submission.permalink)

    def __str__(self):
        return f"{self._submission.permalink} | {self._submission.title}"

    # TODO make return enum describing validation result (instead of t/f)
    def validate_submission_statement(self):  # , min_length):
        # identify and validate submission statement

        # return early if these checks already ran, and ss is proper
        if self._submission_statement_validated:
            # print("\tsubmission statement validated")
            return True

        # text/self posts are exempt from submission statement requirement
        if self._submission.is_self:
            self._is_text_post = True
            self._submission_statement_validated = True
            self._submission_statement = None
            # technically False, but True indicates everything is good, do not remove post
            # print("\tsubmission statement is self post; validated")
            return True

        # identify all candidate submission statements (comments by OP on the post)
        ss_candidates = []
        for reply in self._submission.comments:
            if reply.is_submitter:
                ss_candidates.append(reply)

        if len(ss_candidates) == 0:
            # no submission statement
            self._is_text_post = False
            self._submission_statement_validated = False
            self._submission_statement = None
            # print("\tno submission statement identified; not validated")
            return False
        elif len(ss_candidates) == 1:
            # one comment by OP, assume this is the submission statement
            self._submission_statement = ss_candidates[0]
            self._is_text_post = False
            self._submission_statement_validated = True
            # print("\tsubmission statement identified from single comment; validated")
            return True
        else:
            # multiple comments by OP
            for candidate in ss_candidates:
                text = candidate.body
                text = text.lower().strip().split()
                # this comment includes submission statement, so it is the submission statement
                if "submission" in text and "statement" in text:
                    self._submission_statement = candidate
                    break
                elif "ss" in text:
                    self._submission_statement = candidate
                    break

                # otherwise, take the longest top level comment from OP
                if self._submission_statement:
                    if len(candidate.body) > len(self._submission_statement.body):
                        self._submission_statement = candidate
                else:
                    self._submission_statement = candidate
            # print("\tsubmission statement identified from multiple comments; validated")
            self._is_text_post = False
            self._submission_statement_validated = True
            return True

        # this check is actually done later
        # just check to see if a submission statement exists
        ## 3.) check if submission statement is of proper length
        # if self._submission_statement and (len(self._submission_statement.body) >= min_length):
        #    self._submission_statement_validated = True
        #    return True

        # unable to validate submission statement
        # print("\tunknown case occurred; no submission statement found; not validated")
        self._submission_statement_validated = False
        return False

    def has_time_expired(self):
        # True or False -- has the time expired to add a submission statement?
        return (self._created_time + self._time_limit < datetime.utcnow())

    def is_moderator_approved(self):
        return self._submission.approved

    def is_post_removed(self):
        return self._submission.removed

    def refresh(self, reddit):
        self._submission = praw.models.Submission(reddit, id=self._submission.id)

    def serviced_by_janitor(self, janitor_name):
        # return true if there is a top level comment left by the Janitor
        # don't care if stickied, another mod may have unstickied a comment

        if self._post_was_serviced:
            return True

        for reply in self._submission.comments:
            if reply and reply.author and reply.author.name:
                # print(f"\t\treply from: {reply.author.name}")
                if reply.author.name == janitor_name:
                    self._post_was_serviced = True
                    break

        for report in self._submission.mod_reports:
            if report[-1] == janitor_name:
                print(f"________ found moderator report: {report[0]}_________")
                self._post_was_serviced = True
                break
        return self._post_was_serviced

    def report_post(self, reason):
        self._submission.report(reason)
        self._post_was_serviced = True

    def report_submission_statement(self, reason):
        self._submission_statement.report(reason)
        self._post_was_serviced = True

    def reply_to_post(self, reason, pin=True, lock=False):
        comment = self._submission.reply(reason)
        comment.mod.distinguish(sticky=pin)
        if lock:
            comment.mod.lock()
        self._post_was_serviced = True

    def remove_post(self, reason, note):
        self._submission.mod.remove(spam=False, mod_note=note)
        removal_comment = self._submission.reply(reason)
        removal_comment.mod.distinguish(sticky=True)


###############################################################################
###
### Main worker class -- the bot logic
###
###############################################################################

class Janitor:
    def __init__(self, subreddit):
        self.reddit = praw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            user_agent="my user agent",
            redirect_uri="http://localhost:8080",  # unused for script applications
            username=config.username,
            password=config.password
        )
        self.username = config.username
        self.subreddit = self.reddit.subreddit(subreddit)
        self.mod = self.subreddit.mod
        self.submissions = set()
        self.unmoderated = set()
        self.sub_settings = SubredditSettings()

        self._last_submission_check_time = None
        self._last_unmoderated_check_time = None

    def set_subreddit_settings(self, sub_settings):
        self.sub_settings = sub_settings

    def refresh_posts(self):
        # want to check if post.removed or post.approved, in order to do this,
        # must refresh running list. No need to check the queue or query again
        #
        # this method is necessary because Posts dont have a Reddit property
        for post in self.submissions:
            post.refresh(self.reddit)

        for post in self.unmoderated:
            post.refresh(self.reddit)

    def fetch_submissions(self):
        '''
        will want to split this into checking moderated posts and unmoderated ones,
        why? because the janitor should double check if a mod approved by accident
        (hey, mistakes happen). In this case, it could be reported for false approval
        '''
        one_hour_ago = datetime.utcnow() - timedelta(hours=1, minutes=0)
        one_hour_ago = calendar.timegm(one_hour_ago.utctimetuple())
        submissions = set()
        for post in self.subreddit.top(time_filter="day"):
            # if post.created_utc > one_hour_ago:
            #    submissions.add(Post(post))
            submissions.add(Post(post, self.sub_settings.submission_statement_time_limit_minutes))

        self.submissions = submissions
        return submissions  # for testing, probably don't care about return value

    def fetch_unmoderated(self):
        # loop through filtered posts, want to remove shit without submission statements
        unmoderated = set()
        for post in self.mod.unmoderated():
            # this might be the better one to loop through...
            # why loop through stuff that's already been approved?
            # useful only for double-checking mod actions...
            print("__UNMODERATED__")
            print(post.title)
            unmoderated.add(Post(post, self.sub_settings.submission_statement_time_limit_minutes))
            self.unmoderated.add(Post(post, self.sub_settings.submission_statement_time_limit_minutes))

        # want to remove items from submissions that are in unmoderated
        # and leave unmoderated alone
        self.submissions = self.submissions - unmoderated
        return unmoderated

    def prune_unmoderated(self):
        # want to remove submissions from running list that have been checked
        # for submission statement, that are no longer unmoderated
        self.refresh_posts()

        unmoderated = self.fetch_unmoderated()
        moderated = self.unmoderated - unmoderated
        for post in moderated:
            if post.is_moderator_approved() or post.is_post_removed():
                self.unmoderated.remove(post)

    def prune_submissions(self):
        self.refresh_posts()

        last24h = self.fetch_submissions()
        stale = self.submissions - last24h
        for post in stale:
            if post.is_moderator_approved() or post.is_post_removed():
                self.unmoderated.remove(post)
            else:
                if self.sub_settings.report_old_posts and not post.serviced_by_janitor(self.username):
                    reason = "This post is over 24 hours old and has not been moderated. Please take a look!"
                    self.report_post(reason)
                    post._post_was_serviced = True
                self.unmoderated.remove(post)

        # report anything over 12 hours old that hasn't been serviced
        if self.sub_settings.report_old_posts:
            now = datetime.utcnow()
            for post in self.submissions:
                if post._created_time + timedelta(hours=12, minutes=0) < now and not post.serviced_by_janitor(
                        self.username):
                    if post.is_moderator_approved():
                        print("\tpost already approved by a mod but reported as unmoderated, potentially investigate")
                    else:
                        reason = "This post is over 12 hours old and has not been moderated. Please take a look!"
                        post.report_post(reason)
                        post._post_was_serviced = True

    def handle_posts(self):
        self.refresh_posts()
        all_posts = self.submissions.union(self.unmoderated)

        for post in all_posts:
            print(f"checking post: {post._submission.title}\n\t{post._submission.permalink}...")
            if post.serviced_by_janitor(self.username) or post._submission_statement_validated:
                print("\tpost already serviced")
                continue

            # does the post have low effort flair?
            # yes -> check if post is rule abiding
            #   yes -> continue on to check for submission statement
            #   no -> remove and pin removal reason
            # no -> (NOP)
            if self.sub_settings.post_has_low_effort_flair(post):
                if not self.sub_settings.submitted_during_casual_hours(post):
                    reason = "low effort flair"
                    post.remove_post(self.sub_settings.casual_hour_removal_reason, reason)
                    post._post_was_serviced = True
                    print(f"\tRemoving post: \n\t{post._submission.title}\n\t{post._submission.permalink}")
                    print(f"\tReason: {reason}\n---\n")
                    continue
            else:
                print("\tpost does not have low effort flair")

            # users are given time to post a submission statement
            if post.has_time_expired():
                print("\tTime has expired")
                # check if there is a submission statement
                # yes ->
                # TODO probably should verify ss length in this validate method
                if post.validate_submission_statement():  # self.sub_settings.submission_statement_minimum_char_length):
                    if not post._submission_statement:
                        print("_____________NO SS FOUND__________ DEBUG__________")
                        print(f"post is self? {post._submission.is_self}")
                        print(f"post is validated? {post._submission_statement_validated}")
                        raise Exception("invalid state")
                    print("\tpost has submission statement")
                    # pin submission statement, if subreddit settings require it
                    if self.sub_settings.pin_submission_statement:
                        post.reply_to_post(self.sub_settings.submission_statement_pin_text(post._submission_statement),
                                           pin=True, lock=True)
                        print(
                            f"\tPinning submission statement: \n\t{post._submission.title}\n\t{post._submission.permalink}")

                    # verify submission statements have at least required length, report if necessary
                    if not len(
                            post._submission_statement.body) >= self.sub_settings.submission_statement_minimum_char_length:
                        reason = "Submission statement is too short"
                        if self.sub_settings.report_insufficient_length:
                            post.report_post(reason)
                            print(f"\tReporting post: \n\t{post._submission.title}\n\t{post._submission.permalink}")
                            print(f"\tReason: {reason}\n---\n")
                        else:
                            post.remove_post(self.sub_settings.removal_reason, reason)
                            print(f"\tRemoving post: \n\t{post._submission.title}\n\t{post._submission.permalink}")
                            print(f"\tReason: {reason}\n---\n")
                    else:
                        # print(f"\tSS has proper length: \n\t{post._submission.title}\n\t{post._submission.permalink}")
                        print(f"\tSS has proper length \n\t{post._submission.permalink}")
                else:
                    print("\tpost does NOT have submission statement")
                    now = datetime.utcnow()
                    # did a mod approve, or is it more than 1 day old?
                    #   yes -> report
                    #   no -> remove and pin removal reason
                    if post._created_time + timedelta(hours=24, minutes=0) < now:
                        reason = "Post is more than 1 day old and has no submission statement. Please take a look."
                        post.report_post(reason)
                        print(f"\tReporting post: \n\t{post._submission.title}\n\t{post._submission.permalink}")
                        print(f"\tReason: {reason}\n---\n")
                    elif post.is_moderator_approved():
                        reason = "Moderator approved post, but there is no SS. Please double check."
                        post.report_post(reason)
                        print(f"\tReporting post: \n\t{post._submission.title}\n\t{post._submission.permalink}")
                        print(f"\tReason: {reason}\n---\n")
                    else:
                        reason = "no submission statement"
                        post.remove_post(self.sub_settings.removal_reason, reason)
                        print(f"\tRemoving post: \n\t{post._submission.title}\n\t{post._submission.permalink}")
                        print(f"\tReason: {reason}\n---\n")
                post._post_was_serviced = True

            else:
                print("\tTime has not expired")

                # indicate post serviced by Janitor


def run_forever():
    five_min = 60 * 5
    one_hr = five_min * 12
    while True:
        try:
            cs = CollapseSettings()
            janitor = Janitor("Collapse")
            janitor.set_subreddit_settings(cs)
            janitor.fetch_submissions()
            janitor.fetch_unmoderated()
            counter = 1
            while True:
                # handle posts
                janitor.handle_posts()
                # every 5 min prune unmoderated
                time.sleep(five_min)
                janitor.prune_unmoderated()

                # every 1 hour prune submissions
                if counter == 0:
                    janitor.prune_submissions()
                counter = counter + 1
                counter = counter % 12

            # every hour, check all posts from the day
            # every 5 minutes, check unmoderated queue
        except Exception as e:
            print(e)
            # print("Reddit outage? Restarting....")

        time.sleep(five_min)


def run():
    five_min = 60 * 5
    one_hr = five_min * 12
    cs = CollapseSettings()
    janitor = Janitor("Collapse")
    janitor.set_subreddit_settings(cs)
    janitor.fetch_submissions()
    janitor.fetch_unmoderated()
    counter = 1
    while True:
        # handle posts
        janitor.handle_posts()
        # every 5 min prune unmoderated
        time.sleep(five_min)
        janitor.prune_unmoderated()

        # every 1 hour prune submissions
        if counter == 0:
            janitor.prune_submissions()
        counter = counter + 1
        counter = counter % 12

    # every hour, check all posts from the day
    # every 5 minutes, check unmoderated queue

    time.sleep(five_min)


def run_once():
    cs = CollapseSettings()
    janitor = Janitor("Collapse")
    janitor.set_subreddit_settings(cs)
    # posts = janitor.fetch_submissions()
    # unmoderated = janitor.fetch_unmoderated()
    janitor.fetch_submissions()
    janitor.handle_posts()
    # for post in posts:
    #    print(post.title)
    #    print("___")


if __name__ == "__main__":
    # run_once()
    run()

