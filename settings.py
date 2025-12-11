import re


class Settings:
    # is_dry_run and post_check_frequency_mins should not be overriden
    # set to True to prevent any bot actions (report, remove, comments)
    is_dry_run = False
    post_check_frequency_mins = 5

    report_submission_statement_insufficient_length = False
    report_stale_unmoderated_posts = True
    report_submission_statement_timeout = False

    post_check_threshold_mins = 200 * 60
    consecutive_old_posts = 5
    stale_post_check_frequency_mins = 60
    stale_post_check_threshold_mins = 1 * 60

    submission_statement_pin = True
    submission_statement_time_limit_mins = 30
    submission_statement_minimum_char_length = 150
    submission_statement_bot_prefix = "The following submission statement was provided by"
    # replies to post if ss is invalid
    submission_statement_final_reminder = False
    # replies to ss if ss doesn't contain any keywords with "related to <response>"
    submission_statement_on_topic_reminder = False
    submission_statement_on_topic_keywords = []
    submission_statement_on_topic_response = ""
    submission_statement_on_topic_check_downvotes = False
    submission_statement_on_topic_removal_score = -50000
    submission_statement_on_topic_report_score = 50000
    submission_statement_edit_support = False

    submission_statement_crosspost_prefix = ""

    low_effort_flair = ["casual friday", "low effort", "humor", "humour"]
    
    # Flairs to skip entirely (no submission statement required)
    excluded_flairs = []
    
    ss_removal_reason = ("Your post has been removed for not including a submission statement, "
                         "meaning post text or a comment on your own post that provides context for the link. "
                         "If you still wish to share your post you must resubmit your link "
                         "accompanied by a submission statement of at least "
                         f"{str(submission_statement_minimum_char_length)} characters. "
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
    submission_statement_rule_description = "Submission statements must clearly explain why the linked content is" \
                                            " collapse-related. They should contain a summary or description of the" \
                                            " content and must be at least 150 characters in length. They must be" \
                                            " original and not overly composed of quoted text from the source. If a " \
                                            "statement is not added within thirty minutes of posting it will be removed"

    submission_statement_flair_prefixes = {
        "Placeholder": "asdf",
        # Add more entries for other flair types
    }

    def flair_pin_text(self, flair):
        return self.submission_statement_flair_prefixes.get(flair, "")

    def submission_statement_pin_text(self, ss, prefix):
        header = f"{self.submission_statement_bot_prefix} /u/{ss.author}:\n\n---\n\n"
        footer = f"\n\n---\n\n Please reply to OP's comment here: https://old.reddit.com{ss.permalink}"
        return prefix + "\n\n\n" + header + ss.body + footer


class CollapseSettings(Settings):
    report_stale_unmoderated_posts = True

    submission_statement_crosspost_prefix = ("This post links to another subreddit. "
                                             "Users who are not already subscribed to that subreddit should not "
                                             "participate with comments and up/downvotes, or otherwise harass or "
                                             "interfere with their discussions (brigading)")

    submission_statement_final_reminder = True
    submission_statement_on_topic_reminder = True
    submission_statement_on_topic_keywords = ["adapt",
                                              "airborne",
                                              "bioaccumulation",
                                              "biodiversity",
                                              "biomass",
                                              "boundar",
                                              "breakdown",
                                              "capacity",
                                              "cascad",
                                              "change",
                                              "clathrate",
                                              "climate",
                                              "collaps",
                                              "complex",
                                              "consequence",
                                              "consum",
                                              "crisis",
                                              "deplet",
                                              "depopulation",
                                              "disintegration",
                                              "displac",
                                              "economic",
                                              "ecosystem",
                                              "energy",
                                              "environment",
                                              "eroei",
                                              "exploit",
                                              "exponential",
                                              "externalit",
                                              "extinct",
                                              "failure",
                                              "feedback",
                                              "finite",
                                              "geoengineering",
                                              "global",
                                              "growth",  # infinite growth, limits of growth, etc
                                              "health,"
                                              "heuristic",
                                              "humanity",
                                              "industrial",
                                              "inequal",
                                              "irreversible",
                                              "long now",
                                              "ltg",
                                              "mass starvation",
                                              "microplastic",
                                              "migrat",
                                              "nthe",
                                              "overpopulation",
                                              "oversho",
                                              "peak",
                                              "perverse incentive",
                                              "planet",
                                              "process",
                                              "resilien",
                                              "resource",
                                              "runaway",
                                              "scarcity",
                                              "social",
                                              "societ",
                                              "study",
                                              "supply chain",
                                              "sustain",
                                              "system",
                                              "tipping point",
                                              "uncontrolled",
                                              "unsurvivable",
                                              "wet bulb",
                                              ]
    submission_statement_on_topic_response = "collapse"
    submission_statement_on_topic_check_downvotes = True
    submission_statement_on_topic_removal_score = -3
    submission_statement_on_topic_report_score = 3
    submission_statement_edit_support = True
    submission_statement_flair_prefixes = {
        "Overpopulation": "This thread addresses overpopulation, a fraught but important issue that attracts disruption"
                          " and rule violations. In light of this we have lower tolerance for the following offenses:"
                          "\n\n"
                          "* Racism and other forms of essentialism targeted at particular identity groups people "
                          "are born into."
                          "\n\n"
                          "* Bad faith attacks insisting that to notice and name overpopulation of the human "
                          "enterprise generally is inherently racist or fascist."
                          "\n\n"
                          "* Instructing other users to harm themselves. We have reached consensus that a permaban "
                          "for the first offense is an appropriate response to this, as mentioned in the sidebar."
                          "\n\n"
                          "This is an abbreviated summary of the mod team's statement on overpopulation,"
                          " [view the full statement available in the wiki.]"
                          "(https://www.reddit.com/r/collapse/wiki/claims/#wiki_mod_team_comment_on_overpopulation_posts)"
        # Add more entries for other flair types
    }


class UFOsSettings(Settings):
    # Skip Sighting posts - handled by LocationStatementBot instead
    excluded_flairs = ["sighting"]


class SettingsFactory:
    settings_classes = {
        'collapse': CollapseSettings,
        'ufos': UFOsSettings,
    }

    @staticmethod
    def get_settings(subreddit_name):
        # ensure only contains valid characters
        if not re.match(r'^\w+$', subreddit_name):
            raise ValueError("subreddit_name contains invalid characters")

        settings_class = SettingsFactory.settings_classes.get(subreddit_name.lower(), Settings)
        return settings_class()

        settings_class = SettingsFactory.settings_classes.get(subreddit_name.lower(), Settings)
        return settings_class()
