class Settings:
    # set to True to prevent any bot actions (report, remove, comments)
    is_dry_run = False

    report_submission_statement_insufficient_length = False
    report_stale_unmoderated_posts = True
    report_submission_statement_timeout = False

    post_check_frequency_mins = 5
    post_check_threshold_mins = 2 * 60
    consecutive_old_posts = 5
    stale_post_check_frequency_mins = 60
    stale_post_check_threshold_mins = 12 * 60

    submission_statement_pin = True
    submission_statement_time_limit_mins = 30
    submission_statement_minimum_char_length = 150
    submission_statement_bot_prefix = "The following submission statement was provided by"
    # replies to post if ss is invalid
    submission_statement_final_reminder = False
    # replies to ss if doesn't contain any keywords with "related to <response>"
    submission_statement_on_topic_reminder = False
    submission_statement_on_topic_keywords = []
    submission_statement_on_topic_response = ""

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
    submission_statement_rule_description = "Submission statements must clearly explain why the linked content is" \
                                            " collapse-related. They should contain a summary or description of the" \
                                            " content and must be at least 150 characters in length. They must be" \
                                            " original and not overly composed of quoted text from the source. If a " \
                                            "statement is not added within thirty minutes of posting it will be removed"

    def submission_statement_pin_text(self, ss):
        header = f"{self.submission_statement_bot_prefix} /u/{ss.author}:\n\n---\n\n"
        footer = f"\n\n---\n\n Please reply to OP's comment here: https://old.reddit.com{ss.permalink}"
        return header + ss.body + footer


class CollapseSettings(Settings):
    submission_statement_final_reminder = True
    submission_statement_on_topic_reminder = True
    # copy to a <file>, $ cat <file> | tr "[:upper:]" "[:lower:]" | sort | less
    submission_statement_on_topic_keywords = ["bioaccumulation",
                                              "biomass",
                                              "carrying capacity",
                                              "cascading failure",
                                              "clathrate",
                                              "collapse",
                                              "depopulation",
                                              "energy balance",
                                              "eroei",
                                              "feedback loop",
                                              "future of humanity",
                                              "geoengineering",
                                              "heuristic",
                                              "industrial civilization",
                                              "infinite growth",
                                              "irreversible",
                                              "limits to growth",
                                              "long now",
                                              "ltg",
                                              "mass starvation",
                                              "nthe",
                                              "overpopulation",
                                              "overshoot",
                                              "overshot",
                                              "peak everything",
                                              "peak oil",
                                              "perverse incentive",
                                              "runaway",
                                              "supply chain",
                                              "systematic error",
                                              "systemic problem",
                                              "tipping point",
                                              "uncontrolled",
                                              "unsurvivable without",
                                              "wet bulb",
                                              "wicked problem",
                                              ]
    submission_statement_on_topic_response = "collapse"