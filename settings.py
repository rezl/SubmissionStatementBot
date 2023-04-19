import re


class Settings:
    # is_dry_run and post_check_frequency_mins should not be overriden
    # set to True to prevent any bot actions (report, remove, comments)
    is_dry_run = False
    post_check_frequency_mins = 5

    report_submission_statement_insufficient_length = False
    report_stale_unmoderated_posts = False
    report_submission_statement_timeout = False

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
    # replies to ss if ss doesn't contain any keywords with "related to <response>"
    submission_statement_on_topic_reminder = False
    submission_statement_on_topic_keywords = []
    submission_statement_on_topic_response = ""
    submission_statement_on_topic_check_downvotes = False
    submission_statement_on_topic_removal_score = -50000
    submission_statement_edit_support = False

    low_effort_flair = ["casual friday", "low effort", "humor", "humour"]
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

    def submission_statement_pin_text(self, submission, ss):
        prefix = self.submission_statement_flair_prefixes.get(submission.link_flair_text, "")
        header = f"{self.submission_statement_bot_prefix} /u/{ss.author}:\n\n---\n\n"
        footer = f"\n\n---\n\n Please reply to OP's comment here: https://old.reddit.com{ss.permalink}"
        return prefix + "\n\n\n" + header + ss.body + footer


class CollapseSettings(Settings):
    report_stale_unmoderated_posts = True

    submission_statement_final_reminder = True
    submission_statement_on_topic_reminder = True
    submission_statement_on_topic_keywords = ["adapt",
                                              "bioaccumulation",
                                              "biodiversity",
                                              "biomass",
                                              "capacity",
                                              "cascading failure",
                                              "clathrate",
                                              "collaps",
                                              "complex",
                                              "consum",
                                              "crisis",
                                              "deplet",
                                              "depopulation",
                                              "energy",
                                              "eroei",
                                              "exponential",
                                              "extinct",
                                              "feedback",
                                              "finite",
                                              "geoengineering",
                                              "global",
                                              "growth",  # infinite growth, limits of growth, etc
                                              "heuristic",
                                              "humanity",
                                              "industrial",
                                              "irreversible",
                                              "long now",
                                              "ltg",
                                              "mass starvation",
                                              "nthe",
                                              "overpopulation",
                                              "oversho",
                                              "peak",
                                              "perverse incentive",
                                              "resilien",
                                              "runaway",
                                              "supply chain",
                                              "system",
                                              "tipping point",
                                              "uncontrolled",
                                              "unsurvivable",
                                              "wet bulb",
                                              "wicked problem",
                                              ]
    submission_statement_on_topic_response = "collapse"
    submission_statement_on_topic_check_downvotes = True
    submission_statement_on_topic_removal_score = -3
    submission_statement_edit_support = True
    submission_statement_flair_prefixes = {
        "Overpopulation": "This thread addresses overpopulation, a contentious issue that reliably attracts "
                          "rulebreaking and bad faith arguments, as well as personal attacks. We are regularly"
                          " forced to lock threads, remove comments, and ban users at much higher than normal rates. "
                          "\n\n"
                          "In an attempt to protect the ability of our users to thoughtfully discuss this highly "
                          "charged but important issue, we have decided to warn users that we will be showing lower "
                          "than"
                          " usual tolerance and more readiness to issue bans for comments in the following categories:"
                          "\n\n"
                          "* Racist forms of analysis that blame any specific essential identity group"
                          " (national, religious*, ethnic, etc.) for being too numerous or reproducing \"too much.\""
                          " Critique of class groups (rich/poor) and ideological groups individuals may choose for "
                          "themselves (capitalist/communist, natalist/antinatalist) is still permitted, "
                          "although we will still police comments for violations of Rule 4 covering misinformation,"
                          " for example, the absurd claim that poor people are most responsible for climate change."
                          "\n\n\n"
                          "\t\\* Limited exceptions may be drawn for critique of religious sects and beliefs that"
                          " make a point of priding themselves on their hypernatalism, for example, the quiverfull "
                          "movement and similar social groups making specific natalist choices in the present day."
                          " Please refrain from painting with a broad brush."
                          "\n\n"
                          "* Perhaps more controversially, we have noticed ongoing waves of bad faith attacks "
                          "that insist that any identification or naming of human overpopulation as one of the issues"
                          " contributing to the environmental crisis, as a human predicament, is itself a racist,"
                          " quasi-colonial attack on the peoples of the third world, claiming it is an implicitly"
                          " genocidal take because an identification of overpopulation leads inexorably to a basket"
                          " of \"solutions\" which contains only fascist, murderous tools."
                          "\n\n"
                          "\tFirst, the insistence that population concerns cannot be addressed without murder is "
                          "provably false in light of history's demonstrations that lasting reductions in fertility "
                          "are most effectively achieved by the education, uplifting, and liberation of women and "
                          "girls and the ready availability of contraceptive technology. "
                          "\n\n"
                          "\tSecond, identification of an environmental problem does not"
                          " inherently require there to be any solution at all. Some predicaments cannot be solved, but"
                          " that does not mean it is evil, tyrannical, or heretical to notice, name, and mourn them."
                          " We do not believe observable reality has an ecofascist bent, nor do we believe it is "
                          "credible to require our users to ignore that only 4% of all terrestrial mammalian biomass"
                          " remains wild, with 96% either humans or our livestock. We will not silence our users' "
                          "mourning of the vanishing beauty of the natural world, nor will we enable bad faith attacks"
                          " that insist any defense of, or even observation of, the current state of wild nature in"
                          " light of a human enterprise in massive overshoot is inherently and irredeemably racist. "
                          "Our human numbers are still larger every day than they have ever been, and while "
                          "technologically advanced consumption is a weightier factor causing the narrower issue"
                          " of climate change, the issues of vanishing biodiversity and habitat loss, and the sixth"
                          " mass extinction as a whole, are not so easily laid solely at the feet of rich economies"
                          " and capitalism."
                          "\n\n"
                          "\tIn summary, while we have no clear solutions for convincing humanity to pull itself out of"
                          " its purposeful ecological nosedive, we remain committed to our mission to protect one of"
                          " the few venues for these extremely challenging conversations. In light of this, we will no"
                          " longer allow bad faith claims that identifying human population as an environmental issue"
                          " is inherently racist to be used to shut down discussions. We will use the tools at our"
                          " disposal to enforce this policy, and users should consider themselves warned."
                          "\n\n"
                          "* Comments instructing other users to end their lives will be met with immediate permabans."
                          "\n\n"
                          "We hope these specific rules will further the goals of thoughtful, rational, and "
                          "appropriate discussions of these weighty matters.",
        # Add more entries for other flair types
    }


class SettingsFactory:
    settings_classes = {
        'collapse': CollapseSettings,
        'ufos': Settings,
    }

    @staticmethod
    def get_settings(subreddit_name):
        # ensure only contains valid characters
        if not re.match(r'^\w+$', subreddit_name):
            raise ValueError("subreddit_name contains invalid characters")

        settings_class = SettingsFactory.settings_classes.get(subreddit_name.lower(), Settings)
        return settings_class()
