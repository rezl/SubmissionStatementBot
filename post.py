from datetime import datetime, timedelta


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
