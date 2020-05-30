# Submission Statement Bot
A Reddit bot for requiring submission statements on link posts. If the OP does not include a statement (comment on their own post) within a certain timeframe, the post is removed.

# Requirements
- Python 3.7+
- praw 6.3.1+

# How to Host the Bot on Heroku
This guide assumes you’re using Windows and this bot's code. Although, this guide should work for getting a general Reddit bot running on Heroku as well. The main advantage of Heroku is that their base plan included enough hours to run this bot for free.

# Setup Git
Create a Github account. This is where we’ll be hosting the bot’s code.
Go to the bot repo and select ‘fork’ to create a copy of it to on your own github account. 
From your new repo, select ‘Clone or download’ and then ‘Download ZIP’ to download a local copy. We’ll come back to this later.
Make note of (copy/paste somewhere) your Reddit app’s Client ID. This the string directly under ‘personal use script’. This is your Reddit App Client ID.
Make note of (copy/paste somewhere) the URL linking to your repo (e.g. https://github.com/yourusername/collapse). This is your Github Repo URL.
Go here and install Git if you don’t have it already.


# Setup Heroku
Create a Heroku account. This is the service which will be running the bot.
Once created, create a new Heroku app.
Add an app name and select ‘create app’
On the following page (Deploy) make sure Deployment method is set to Heroku Git (should be by default)
Click the ‘Settings’ tab to go to your app’s settings page. Make note of  (copy/paste somewhere)  the Heroku git URL, we’ll need it later. This is your Heroku Git URL.
Click ‘Deploy” tab to go to the deploy instructions. Keep this open for later.
Install Heroku SLI. This will allow us to manage the app via a terminal.


# Setup Reddit
Create a new Reddit account with the name you’d like for your bot.
Login into your primary Reddit account which moderates your subreddit.
Go to https://old.reddit.com/r/YOURSUBREDDIT/about/moderators/ and invite the bot to become a moderator with full permissions.
Log back into the bot’s accounts and accept the invitation.
Go to https://old.reddit.com/prefs/apps/ and select ‘Create and app’
Type a name for your app and choose ‘script’.
Write a short description of what your bot will be doing.
Set the 'about' URI to your Github Repo URL.
Set the 'redirect' URI to your Heroku Git URL. 
Select ‘create app’.
Make note of the secret code for the next steps.


# Configure the Bot
Take the local copy of your repo and extract  it to wherever you’d like it to live. I put it at the root of my hard drive (e.g. c:/mybot) so I don’t have to type out the path once we’re in the terminal.
Open bot.py
Change the number in RGX_SENTENCE_3 to set the minimum number of characters you want to require for the bot to consider a submission statement valid (default is fifty).
Change SUB_NAME to your sub’s name. 
Set the REMOVAL_REPLY text to whatever you’d like the bot to comment after removing a post
Change the line: if post_time <= dt(2020, 5, 27, 0, 0): 
The section ‘2020, 5, 27,’ is a date (year, month, day). The bot will not remove posts submitted earlier than this date. This is important, since you don’t want it retroactively removing all the posts on your subreddit since the beginning of time. 
Save the file.
Open config.py and fill in these fields with your info. Make sure not to remove the apostrophes surrounding them:
username = 'BotRedditUsername'
password = 'BotRedditPassword'
client_id = 'RedditAppClientID'
client_secret = 'RedditAppSecret'
Save the file.


# Upload the Bot
Open Git Bash (Windows key, then type Git Bash).
$ heroku login
It you press enter this will open a browser window and have you login to Heroku.
The terminal should say you’re logged in now. If it hangs, try this.
The next steps can be referenced in the Deploy tab on the Heroku site.
$ cd c:folderyourbotisin
$ git init
$ heroku git:remote -a yourbotname
$ git add .
$ git commit -am "make it better"
$ git push heroku master
Once it is it done deploying, go to back to the Heroku page.
Select the ‘Resources’ tab.
Click the pen icon next to ‘worker python bot.py’
Now click the toggle to the left of the pen to activate the process. It should turn blue.
Click confirm.
Select More > View logs
Watch the bot in action!


# Upgrade your Heroku hours
Go to the Heroku billing page (https://dashboard.heroku.com/account/billing) and add a credit card to your account. 
Heroku limits the number of hours they will run your bot. We can increase these by attaching a credit card to your account. Your bot will not use up it’s free monthly allowance, but will not have enough free hours without a card attached.



# Other related guides:
https://github.com/kylelobo/Reddit-Bot#deploying_the_bot

https://github.com/Visovsiouk/reddit-watchbot

https://pythontips.com/2017/04/13/making-a-reddit-facebook-messenger-bot/

https://github.com/mconstanza/redditBotHackathon

