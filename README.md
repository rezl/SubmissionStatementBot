# Submission Statement Bot
** Times (5 min, 30 min, etc) and actions (remove, report) provided in this guide are recommended defaults, however most are configurable via updating script

This is a Reddit bot primarily for handling submission statements on link posts:
- every 5 min, handles new posts submission statement to comment ss, report, or remove post
- every 5 min, removes new posts if low effort flaired and outside Casual Friday
- every hour, reports old unmoderated posts

New posts = based on "new" post sort, all posts until 5 consecutive posts older than 2 hours are found
(consecutive is required to ensure automod-held posts older than 2 hours are still actioned)\
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


# Requirements
- Python 3.10+
- praw 6.3.1+

# BOT SETUP

## Setup Git
1. [Create a Github account.](https://github.com/join)

2. [Go here and install Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) if you don’t have it already.

3. [Assuming you're reading this on the repo page](https://github.com/rezl/SubmissionStatementBot), select ‘fork’ to create a copy of it to your Github account. 

4. From your new repo, select **Code** and then under **Clone** copy the HTTPS URL (e.g. https://github.com/rezl/SubmissionStatementBot.git) to download a local copy

![img.png](img.png)

5. Navigate to a folder you want a local copy of the repo to live, and clone the Github repo to your local PC:
   1. It's up to you where to put the repo - recommended in a folder like C:\<username>\Documents\ or a new folder, C:\<username>\Documents\Programming
   2. `git clone <url>`
      1. e.g. `git clone https://github.com/rezl/SubmissionStatementBot.git`
   3. Make note of (copy/paste somewhere) of the folder you clone to for future reference

6. Make note of (copy/paste somewhere) your Reddit app’s Client ID. This the string directly under **personal use script**. This is your Reddit App Client ID.

7. Make note of (copy/paste somewhere) the URL linking to your repo (e.g. https://github.com/yourusername/collapse). This is your Github Repo URL.


## Setup Reddit
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


## Configure the Bot
1. Open the folder containing local copy of your repo from Setup Git > step 5

2. Open **bot.py**

3. Change settings how you'd like:
* `report_*`: how the bot handles the individual scenarios
* `*_frequency_mins`: how often the bot will check this scenario (new posts, old posts)
* `*_threshold_mins`: what posts the bot will review for each scenario (newer than threshold, older than threshold)
* `submission_statement_minimum_char_length`: minimum number of characters you want to require for the bot to consider a submission statement valid (default is 150)
* `*_removal_reason`: bot responses when removing for these reasons
* `low_effort_flair`: flairs which should not be used outside casual friday

5. Save the file.

6. If not configured in Fly.io (Setup Fly step 9), Open **config.py** and fill in these fields with your info. Make sure not to remove the apostrophes surrounding them.
```
BOT_USERNAME = 'BotRedditUsername'
BOT_PASSWORD = 'BotRedditPassword'
CLIENT_ID = 'RedditAppClientID'
CLIENT_SECRET = 'RedditAppSecret'
SUBREDDIT = 'SomeSubreddit'
```
When config is not provided in Fly, the bot will attempt to use config from this file.

9. Save the file.

10. Optionally run the bot locally - "is_dry_run" can be set to "True" to run the bot without it making any changes (report, remove, reply to posts)


## Setup Fly.io
- The main advantage of Fly.io is their base (hobby) plan includes enough hours to host this bot for free. This guide assumes you’re using Windows and this bot's code, but should work for getting a general Reddit bot running on Fly.io as well.
- Hosting this bot alongside other apps in your Fly account may incur costs if the cumulative resource usage is beyond free limits

1. Create a Fly account. This is the service which will be running the bot.

2. Create your new Fly application from the command line, references:
   1. [Speedrun setup](https://fly.io/docs/speedrun/)
   2. Fly.io webpage, cannot create Python apps from here, reference only ([main page](https://fly.io/dashboard/personal) > ["Launch an App"](https://fly.io/dashboard/personal/launch))
   3. [Non-fly guide](https://jonahlawrence.hashnode.dev/hosting-a-python-discord-bot-for-free-with-flyio)

3. Open powershell on your PC from Windows search "Windows Powershell"

4. Install fly.io tooling by copy pasting this command into the powershell terminal:
   1. https://fly.io/docs/hands-on/install-flyctl/#windows
   2. `iwr https://fly.io/install.ps1 -useb | iex`

5. Log in to fly from your terminal with:
   1. https://fly.io/docs/hands-on/sign-in/
   2. `flyctl auth login`

6. Navigate to the folder you extracted or cloned the git repo to (Setup Git > step 7)

7. Launch a new app to fly.io with:
   1. https://fly.io/docs/hands-on/launch-app/
      1. You will want to override the existing fly.toml file, as the app name is included in this file
   2. `flyctl launch`

8. Verify you see the fly app on your [fly webpage](https://fly.io/dashboard)

9. Add the required config for your bot to Fly.io (added to Fly to keep sensitive info private) via command line:
   1. app page (https://fly.io/apps/<appname>) > Secrets
   2. Reference: https://fly.io/docs/reference/secrets/#setting-secrets
   3. `flyctl secrets set BOT_USERNAME=BotRedditUsername`
   4. Add your each secret individually with above command (after set, they are encrypted and not readable):
```
BOT_USERNAME=BotRedditUsername
BOT_PASSWORD=BotRedditPassword
CLIENT_ID=RedditAppClientID
CLIENT_SECRET=RedditAppSecret
SUBREDDIT=SomeSubreddit
``` 

10. Deploy your new app to fly.io with:
    1. https://fly.io/docs/hands-on/launch-app/ > "Next: Deploying Your App"
    2. `flyctl deploy`

11. Monitor app from Fly.io, or command line:
    1. https://fly.io/apps/<app-name>
    2. https://fly.io/apps/<app-name>/monitoring
    3. `flyctl status`
    4. You should now see the bot in action. You can check your subreddit to see whatever changes it made (if any) as well as make a test post to ensure it's working properly.


## Integrate Fly.io and Github for automatic deployments
- Automatically deploys your code to Fly.io when changes are pushed to the Github repo's master branch
- Without this step, you will manually deploy the app from command line as needed with `flyctl deploy`

1. Obtain an authentication token, which will tell fly.io which application you are deploying to:
   1. On command line, `flyctl auth token`

2. From your Github forked repo, add this auth token as a secret
   1. [Non-fly guide](https://jonahlawrence.hashnode.dev/hosting-a-python-discord-bot-for-free-with-flyio#heading-continuous-deployment-from-github)
   2. Go to your repo's Settings > Secrets > Actions and click New repository secret

3. Now, whenever you add to your repo's master branch, it will automatically deploy to fly.io
   1. You can prevent automatic deployments by removing this auth token from github, or removing the fly.yml file (.github/workflows/fly.yml)
   2. You can cancel individual deployments whilst it's running:
      1. Navigate to Actions Page (https://github.com/<username>/<reponame>/actions), which lists all previous and ongoing deployments
      2. Click on the current deployment (yellow circle) > Cancel Workflow 


# Other related guides:
[🤖 Making a Reddit Bot using Python and Heroku](https://github.com/kylelobo/Reddit-Bot#deploying_the_bot)

[Reddit Watchbot](https://github.com/Visovsiouk/reddit-watchbot

[Making a Reddit + Facebook Messenger Bot](https://pythontips.com/2017/04/13/making-a-reddit-facebook-messenger-bot/)

[RedditBotTest](https://github.com/mconstanza/redditBotHackathon)

Credit goes to [epicmindwarp](https://github.com/epicmindwarp) for writing this bot. I decided to document the process for getting it up and running on Heroku for free so it can potentially be more available to various moderators. You can currently see this bot running over at [r/collapse](https://reddit.com/r/collapse) as [CollapseBot](https://reddit.com/user/collapsebot).
