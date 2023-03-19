import asyncio
import typing

import discord
from discord.ext import commands

from settings import Settings


class DiscordClient(commands.Bot):
    def __init__(self, error_guild_name, error_guild_channel):
        super().__init__('#', intents=discord.Intents.all())
        self.error_guild_name = error_guild_name
        self.error_channel_name = error_guild_channel
        self.error_guild = None
        self.error_channel = None
        self.is_ready = False

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        self.error_guild = discord.utils.get(self.guilds, name=self.error_guild_name)
        self.error_channel = discord.utils.get(self.error_guild.channels, name=self.error_channel_name)
        self.is_ready = True
        guilds_msg = "\n".join([f"\t{guild.name}" for guild in self.guilds])
        startup_message = f"{self.user} is in the following guilds:\n" \
                          f"{guilds_msg}"
        print(startup_message)
        await self.error_channel.send(f"I am online for SubmissionStatement script, is_dry_run={Settings.is_dry_run}")

    def send_error_msg(self, message):
        full_message = f"SubmissionStatement script has had an exception. This can normally be ignored, " \
                       f"but if it's occurring frequently, may indicate a script error.\n{message}"
        if self.error_channel:
            asyncio.run_coroutine_threadsafe(self.error_channel.send(full_message), self.loop)

    def add_commands(self):
        @self.command(name="ping", description="lol")
        async def ping(ctx):
            prefix = "DRY RUN" if Settings.is_dry_run else "DO REAL SHIT"
            dry_run = f"I'm currently running in {prefix} mode"
            await ctx.channel.send(dry_run)

        @self.command(name="set_dry_run", brief="Set whether bot can make permanent reddit actions (0/1)",
                      description="Change whether this bot can make reddit actions (usernotes, comments). "
                                  "When in dry_run, the bot will not make usernotes or reddit comments, "
                                  "however the full workflow otherwise is available on discord\n"
                                  "Include: \n"
                                  "  * 0 (not in dry run, makes actions)\n"
                                  "  * 1 (dry run, no reddit actions)",
                      usage=".set_dry_run 1")
        async def set_dry_run(ctx, dry_run: typing.Literal[0, 1] = 1):
            Settings.is_dry_run = dry_run
            if Settings.is_dry_run:
                await ctx.channel.send(f"I am now running in dry run mode")
            else:
                await ctx.channel.send(f"I am now NOT running in dry run mode")
