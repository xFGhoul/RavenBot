import discord
import DiscordUtils
import datetime
import time
from datetime import datetime
from typing import Optional


from discord.ext import commands, tasks
from discord.ext.commands import BucketType
from discord.utils import get

from tortoise.expressions import F


from models import Invites, Guild
from utils.logging import log


class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracker = DiscordUtils.InviteTracker(bot)
        self.send_leaderboard.start()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.tracker.cache_invites()
        log.info("Invites Cache Ready.")

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.tracker.update_invite_cache(invite)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.tracker.update_guild_cache(guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.tracker.remove_invite_cache(invite)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.tracker.remove_guild_cache(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        # inviter is the member who invited
        if member.bot:
            return None

        if time.time() - member.created_at.timestamp() < 2492000:
            warn_member_channel = get(member.guild.text_channels, id=816442042150289448)
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"{member.mention}'s Account is less than 3 days old. Therefore the invite is discarded."
            )
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            await warn_member_channel.send(embed=embed)
            return
            
        inviter = await self.tracker.fetch_inviter(member)

        if not inviter: 
            return

        guild = await Guild.get(discord_id=member.guild.id)
        record, created_new = await Invites.get_or_create(inviter_id=inviter.id, guild=guild, defaults={'invite_count': 1})
        if not created_new:
            record.invite_count = F('invite_count') + 1
            await record.save(update_fields=['invite_count'])
            await record.refresh_from_db(fields=['invite_count'])
        
    
        invite_log_channel = get(member.guild.text_channels, id=816442042150289448)
        embed = discord.Embed(
            color=discord.Color.blue(),
            description=f"{inviter.mention} has Invited {member.mention}, they now have a total of `{record.invite_count}` Invites!"
        )
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        await invite_log_channel.send(embed=embed)

    @commands.group()
    @commands.guild_only()
    async def invites(self, ctx, member: Optional[discord.Member]) -> None:
        if ctx.invoked_subcommand is not None:
            return None

        if member is None:
            member = ctx.author

        if member.bot:
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"Bots cannot have any invites."
            )
            await ctx.send(embed=embed)
            return None

        guild = await Guild.get_or_none(discord_id=ctx.guild.id)
        invite_user = (await Invites.get_or_create(inviter_id=member.id, guild=guild))[0]

        num_of_invites = invite_user.invite_count

        embed = discord.Embed(
            color=discord.Color.blue(),
            description=f"{member.mention} has `{num_of_invites}` Invites."
        )
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        await ctx.send(embed=embed)

    @invites.command(name="leaderboard", aliases=['lb', 'board'])
    @commands.guild_only()
    async def invite_lb(self, ctx):
        guild = await Guild.get_or_none(discord_id=ctx.guild.id)
        invite_lb = await Invites.filter(guild=guild).order_by('-invite_count').limit(25).all()

        embed = discord.Embed(
            title="Top Inviters",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        for invite in invite_lb:
            embed.add_field(name=ctx.guild.get_member(invite.inviter_id), value=f"Invites: `{invite.invite_count}`", inline=False)
        await ctx.send(embed=embed)

    @tasks.loop(seconds=3600)
    async def send_leaderboard(self):
        db_guild = await Guild.get_or_none(discord_id=709325285518213150)
        invite_lb = await Invites.filter(guild=db_guild).order_by('-invite_count').limit(25).all()
        guild = self.bot.get_guild(709325285518213150)
        inv_channel = self.bot.get_channel(816479943751761920)
        message = await inv_channel.fetch_message(816506295679057941)
        
        
        embed = discord.Embed(
            title="Top Inviters",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        for invite in invite_lb:
            embed.add_field(name=guild.get_member(invite.inviter_id), value=f"Invites: `{invite.invite_count}`", inline=False)
        await message.edit(embed=embed)
        log.info("Upgraded LB")


    @send_leaderboard.before_loop
    async def before_printer(self):
        print('Loading Invite LB...')
        await self.bot.wait_until_ready()

def setup(bot):
    cog = InviteTracker(bot)
    bot.loop.create_task(cog.on_ready())
    bot.add_cog(cog)