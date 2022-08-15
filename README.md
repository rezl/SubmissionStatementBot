# Submission Statement Bot
This is a Reddit bot primarily for handling submission statements on link posts:
- every 5 min, handles new posts submission statement to comment ss, report, or remove post
- every 5 min, removes new posts if low effort flaired and outside Casual Friday
- every hour, reports old unmoderated posts

New posts = less than 2 hours old\
Old posts = older than 12 hours 

## Submission statement handling
After 30 min it will find the submission statement and:
- if the ss is the post text, does nothing
- if the submission statement is "valid" (>150 chars), comments this with sticky distinction
- if the ss is missing, removes it
- if the ss is <150 chars, reports it
- if the ss is mod approved but missing ss, reports it


### How does it find the submission statement?
Preferentially takes the post text as submission statement. If that is too short, immediately comments saying so

If there is no post text, or it's too short, at 30 min it will find a submission statement in the OP's top level comments
- preferentially takes a comment including "ss", "submission" or "statement"
- otherwise takes the longest comment by OP

### TODO
- post the ss as soon as it's found (not waiting for 30 min)
- when OP has posted a non-ss comment OR post has been live 15 min, comment saying the post is still missing a ss
- handle user edits to their ss (currently, you can delete a bots ss for it to repost if user edits, provided the post is still less than 2 hours old)



# Requirements
- Python 3.10+
- praw 6.3.1+

# How to Host the Bot on Heroku
The main advantage of Heroku is their base plan includes enough hours to host this bot for free. This guide assumes you’re using Windows and this bot's code, but should work for getting a general Reddit bot running on Heroku as well. 

# Setup Git
1. [Create a Github account.](https://github.com/join) 

2. [Assuming you're reading this on the repo page](https://github.com/rezl/SubmissionStatementBot), select ‘fork’ to create a copy of it to your Github account. 

3. From your new repo, select **Clone or download** and then **Download ZIP** to download a local copy. We’ll come back to this later.

4. Make note of (copy/paste somewhere) your Reddit app’s Client ID. This the string directly under **personal use script**. This is your Reddit App Client ID.

5. Make note of (copy/paste somewhere) the URL linking to your repo (e.g. https://github.com/yourusername/collapse). This is your Github Repo URL.

6. [Go here and install Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) if you don’t have it already.


# Setup Heroku
1. Create a Heroku account. This is the service which will be running the bot.

2. Once created, create a new Heroku app.

3. Add an app name and select **create app**

4. On the following page (Deploy) make sure Deployment method is set to **Heroku Git** (should be by default)

5. Click the **Settings** tab to go to your app’s settings page. Make note of  (copy/paste somewhere)  the Heroku git URL, we’ll need it later. This is your Heroku Git URL.

6. Add the required config for your bot to Heroku (added to Heroku to keep sensitive info private)
    * **Settings** tab > Config Vars > Reveal Config Vars
    * Add your config individually as a Config Var:
```
BOT_USERNAME = BotRedditUsername
BOT_PASSWORD = BotRedditPassword
CLIENT_ID = RedditAppClientID
CLIENT_SECRET = RedditAppSecret
SUBREDDIT = SomeSubreddit
```

7. Click the **Deploy** tab to load up the Deploy Instructions. Keep this open for later.

8. Install Heroku SLI. This will allow us to manage the app via a terminal.

9. Bot is compatible with heroku stack version 22



# Setup Reddit
1. [Create a new Reddit account](https://www.reddit.com/register/?dest=https%3A%2F%2Fwww.reddit.com%2F) with the name you’d like for your bot.

2. Login into your primary Reddit account which moderates your subreddit.

3. Go to https://old.reddit.com/r/YOURSUBREDDIT/about/moderators/ and invite the bot to become a moderator with full permissions.

4. Log back into the bot’s account and accept the invitation.

5. Go to https://old.reddit.com/prefs/apps/ and select **Create and app**

6. Type a name for your app and choose **script**.

7. Write a short description of what your bot will be doing.

8. Set the **about URI** to your Github Repo URL.

9. Set the **redirect URI** to your Heroku Git URL. 

10. Select **create app**.

11. Make note of the secret code for the next steps.


# Configure the Bot
1. Take the local copy of your repo and extract it to wherever you’d like it to live on your machine. I put it at the root of my hard drive (e.g. c:/mybot) so I don’t have to type out a longer path once we’re in the terminal, but it's just personal preference.

2. Open **bot.py**

3. Change settings how you'd like:
* `report_*`: how the bot handles the individual scenarios
* `*_frequency_mins`: how often the bot will check this scenario (new posts, old posts)
* `*_threshold_mins`: what posts the bot will review for each scenario (newer than threshold, older than threshold)
* `submission_statement_minimum_char_length`: minimum number of characters you want to require for the bot to consider a submission statement valid (default is 150)
* `*_removal_reason`: bot responses when removing for these reasons
* `low_effort_flair`: flairs which should not be used outside casual friday

5. Save the file.

6. If not configured in Heroku (#Setup Heroku step 6), Open **config.py** and fill in these fields with your info. Make sure not to remove the apostrophes surrounding them.
```
BOT_USERNAME = 'BotRedditUsername'
BOT_PASSWORD = 'BotRedditPassword'
CLIENT_ID = 'RedditAppClientID'
CLIENT_SECRET = 'RedditAppSecret'
SUBREDDIT = 'SomeSubreddit'
```
When config is not provided in Heroku, the bot will attempt to use config from this file.

9. Save the file.

10. Optionally run the bot locally - "is_dry_run" can be set to "True" to run the bot without it making any changes (report, remove, reply to posts)

# Upload the Bot
1. Open **Git Bash** (Windows key, then type `Git Bash`).

2. Type `heroku login` in the terminal. This will open a browser window and have you login to Heroku. The terminal should say you’re logged in now. If it hangs, [try this](https://stackoverflow.com/questions/55955948/heroku-login-success-but-then-freezes). The next commands you're need to enter can also be referenced in the Deploy tab on the Heroku site.
```
$ cd c:folderyourbotisin

$ git init

$ heroku git:remote -a yourbotname

$ git add .

$ git commit -am "make it better"

$ git push heroku master
````
3. Once it is it done deploying go to back to the Heroku page.

4. Select the **Resources** tab.

5. Click the pen icon next to **worker python bot.py**

6. Click the toggle to the left of the pen to activate the process. It should turn blue.

7. Click confirm. This will start running the bot process.

8. Select **More** and **View logs**

9. You should now see the bot in action. You can check your subreddit to see whatever changes it made (if any) as well as make a test post to ensure it's working properly.


# Upgrade your Heroku hours
Optional: go to the Heroku billing page (https://dashboard.heroku.com/account/billing) and add a credit card to your account. 
Heroku limits the number of hours they will run your bot each month. This can be increased by attaching a credit card to the account. This bot will not use up it’s free monthly allowance, but will not have enough free hours without a card attached.



# Other related guides:
[🤖 Making a Reddit Bot using Python and Heroku](https://github.com/kylelobo/Reddit-Bot#deploying_the_bot)

[Reddit Watchbot](https://github.com/Visovsiouk/reddit-watchbot

[Making a Reddit + Facebook Messenger Bot](https://pythontips.com/2017/04/13/making-a-reddit-facebook-messenger-bot/)

[RedditBotTest](https://github.com/mconstanza/redditBotHackathon)

Credit goes to [epicmindwarp](https://github.com/epicmindwarp) for writing this bot. I decided to document the process for getting it up and running on Heroku for free so it can potentially be more available to various moderators. You can currently see this bot running over at [r/collapse](https://reddit.com/r/collapse) as [CollapseBot](https://reddit.com/user/collapsebot).
