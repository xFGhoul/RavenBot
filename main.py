import discord
import yaml
import datetime
import asyncio
import watchgod
import inspect
import itertools
import logging
import os
import asyncio
import traceback
import warnings

from typing import Any, Mapping, Tuple
from asyncio import sleep
from glob import glob

from discord.flags import MemberCacheFlags
from discord import Intents, Embed, AllowedMentions
from discord.ext import commands, tasks

from rich.traceback import install
from rich import print
from rich.logging import RichHandler

from tortoise import Tortoise
from rich.traceback import install


from utils.rich import console
from models import Guild
from config.loader.configloader import config
from db.tortoise_config.tortoise import TORTOISE_CONFIG


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("rich")

class RavenBot(commands.Bot):

    def __init__(self, extensions_dir: str = 'cogs', *args, **kwargs):
        
        self.extensions_dir = extensions_dir

        self.activities = itertools.cycle((
            discord.Activity(type=discord.ActivityType.watching, name='-help'),
            lambda: discord.Activity(type=discord.ActivityType.listening,
                                     name=f'{len(bot.commands)} Commands | {len(bot.users)} Users')
        ))

        # Declaring intents and initalizing parent class
        
        intents = Intents.default()
        intents.presences = True
        intents.members = True
        stuff_to_cache = MemberCacheFlags.from_intents(intents)
        mentions = AllowedMentions(everyone=False, roles=False)
        super().__init__(
            intents=intents,
            command_prefix=self.determine_prefix,
            case_insensitive=True,
            allowed_mentions=mentions,
            member_cache_flags=stuff_to_cache,
            chunk_guilds_at_startup=False,
            max_messages=1000,


            *args, **kwargs
        )


        self.load_extensions()
        
        try:
            self.load_extension("jishaku")
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
        

    async def determine_prefix(self, bot: commands.Bot, message: discord.Message) -> str:
        """Determines the prefix to use for command invocation

        Parameters
        ----------
        bot : commands.Bot
            The bot that is running
        message : discord.Message
            The message to determine the prefix for

        Returns
        -------
        str
            The prefix for the guild the message is in
        """
        guild = message.guild
        if guild:
            return commands.when_mentioned_or('-')(bot, message)
        else:
            return

    def load_extensions(self, reraise_exceptions: bool = False) -> Tuple[Tuple[str], Tuple[str]]:
        """Loads all extensions

        Parameters
        ----------
        reraise_exceptions : bool, optional
            Weather or not to silently continue on error, or raise the exception, by default False

        Returns
        -------
        Tuple[Tuple[str], Tuple[str]]
            A tuple containing a tuple of extensions that loaded successfully,
            followed by a tuple of extensions that failed to load

        Raises
        ------
        commands.ExtensionFailed
            There was an error during loading the extension, you can use the 'original'
            atrribute of this exception ot get more details
        commains.NoEntryPointError
            The extension didn't have a setup function visible at the global scope level
        commands.ExtensionAlreadyLoaded
            The extension was already loaded
        commands.ExtensionNotFound
            The path provided contained no valid extensions
        """
        loaded_extensions = set()
        failed_extensions = set()
        for file in map(lambda file_path: file_path.replace(os.path.sep, '.')[:-3], glob(f'{self.extensions_dir}/**/*.py', recursive=True)):
            try:
                self.load_extension(file)
                loaded_extensions.add(file)
                console.print(f'[bold green][MODULE][/bold green] [bold cyan]{file} loaded.[/bold cyan]')
            except Exception as e:
                failed_extensions.add(file)
                console.print(f"[bright red][MODULE ERROR][/bright red] [bold cyan]Failed to load COG {file}[/bold cyan]")
                if not reraise_exceptions:
                    traceback.print_exception(type(e), e, e.__traceback__)
                else:
                    raise e
        result = (tuple(loaded_extensions), tuple(failed_extensions))
        return result

    def launch(self) -> None:
        TOKEN = os.getenv("DISCORD_TOKEN")
        self.run(TOKEN, reconnect=True, bot=True)

    @tasks.loop(seconds=10)
    async def status(self):
        """Cycles through all status every 10 seconds"""
        new_activity = next(self.activities)
        # The commands one is callable so the command counts actually change
        if callable(new_activity):
            await self.change_presence(status=discord.Status.online, activity=new_activity())
        else:
            await self.change_presence(status=discord.Status.online, activity=new_activity)

    @status.before_loop
    async def before_status(self) -> None:
        """Ensures the bot is fully ready before starting the task"""
        await self.wait_until_ready()

    async def on_ready(self) -> None:
        """Called when we have successfully connected to a gateway"""
        
        console.print(f'Signed into Discord as [bold cyan]{self.user}[/bold cyan] (ID: [bold cyan]{self.user.id}[/bold cyan])')
        console.print(f'Running Development On Discord Version:[bold cyan]{discord.__version__}[/bold cyan]')
    
        # Initialize Tortoise ORM and start background tasks
        try:
            await Tortoise.init(TORTOISE_CONFIG)
            console.print("[bold green]Initialized RavenBot Database[/bold green]")
        except Exception as e:
            log.exception(e)
        self.status.start()
        self.cog_watcher_task.start()

# Defining root level commands
bot = RavenBot()


@bot.command()
@commands.is_owner()
async def shutdown(ctx) -> None:
    """Shuts down the bot"""
    await ctx.send("Logging out.")
    await ctx.message.add_reaction(":white_check_mark:")
    await bot.logout()

@shutdown.error
async def shutdown_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='You do not have the permissions to do that!'
        )
        await ctx.send(embed=embed)
    else:
        traceback.print_exception(type(error), error, error.__traceback__)


@bot.command()
@commands.is_owner()
async def load(ctx, extention: str) -> None:
    """Loads an extension, owners only"""
    bot.load_extension(f'cogs.{extention}')
    embed = discord.Embed(
        color=discord.Color.dark_blue(),
        description=f'`{extention}` Loaded Successfully!'
    )
    await ctx.send(embed=embed)


@load.error
async def load_error(ctx, error) -> None:
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This can only be used by the bot\'s owners!'
        )
    elif isinstance(error, commands.ExtensionAlreadyLoaded):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This Extension is already loaded!'
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.ExtensionNotFound):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This Extension does not exist!'
        )
        await ctx.send(embed=embed)
    else:
        traceback.print_exception(type(error), error, error.__traceback__)


@bot.command()
@commands.is_owner()
async def unload(ctx, extention) -> None:
    """Unloads an extension, owners only"""
    bot.unload_extension(f'cogs.{extention}')
    embed = discord.Embed(
        color=discord.Color.dark_blue(),
        description=f'{extention} Cog has been disabled'
    )
    await ctx.send(embed=embed)


@unload.error
async def unload_error(ctx, error) -> None:
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This can only be used by the bot\'s owners!'
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.ExtensionNotLoaded):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This Extension is not loaded!'
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.ExtensionNotFound):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This Extension does not exist!'
        )
        await ctx.send(embed=embed)
    else:
        traceback.print_exception(type(error), error, error.__traceback__)


@bot.command()
@commands.is_owner()
async def cogs(ctx) -> None:
    """Shows all loaded extensions, owners only"""
    cogs = []

    for cog in bot.cogs:
        cogs.append(f"`{cog}`")

    cogs_str = ', '.join(cogs)
    embed = discord.Embed(
        title=f"All Cogs",
        description=cogs_str,
        colour=discord.Color.dark_blue()
    )
    embed.set_footer(
        text=f'You can always do {ctx.prefix}help to see all cog features!')
    await ctx.send(embed=embed)


@cogs.error
async def cogs_error(ctx, error) -> None:
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This can only be used by the bot\'s owners!'
        )
        await ctx.send(embed=embed)
    else:
        traceback.print_exception(type(error), error, error.__traceback__)


@bot.command()
@commands.is_owner()
async def reload(ctx, extension) -> None:
    """Reloads an extension, owners only"""
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    embed = discord.Embed(title=':white_check_mark: **Successfully reloaded ' + extension + '.**')
    await ctx.send(embed=embed)


@reload.error
async def reload_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This can only be used by the bot\'s owners!'
        )
    elif isinstance(error, commands.ExtensionNotLoaded):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This extension is not loaded!'
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.ExtensionNotFound):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            description='This extension does not exist!'
        )
        await ctx.send(embed=embed)
    else:
        traceback.print_exception(type(error), error, error.__traceback__)


if __name__ == '__main__':
    try:
        install()
        bot.launch()
    except Exception as e:
        log.exception(e)
