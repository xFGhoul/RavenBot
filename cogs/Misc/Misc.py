import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, BucketType, cooldown

from datetime import timedelta
import datetime

import asyncio
import time
import math
import random
import json


class Miscellaneous(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		
	#Gives info about the user!
	@commands.command(aliases=['user', 'userinfo'])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def whois(self, ctx, user: discord.Member = None):
		if not user:
			user = ctx.author

		mentions = [role.mention for role in user.roles]
		roles = mentions[1:]
		no_of_roles = len(roles)
		fmt = "%a, %b %d, %Y, %I:%M %p"
		created_at = user.created_at.strftime(fmt)
		joined_at = user.joined_at.strftime(fmt)
		permission = []


		for perms in user.guild_permissions:
			if "administrator" in perms and 'True' in str(perms[1]):
				permission.append('Administrator')
			if "manage_guild" in perms and 'True' in str(perms[1]):
				permission.append('Manage Server')
			if "manage_nicknames" in perms and 'True' in str(perms[1]):
				permission.append('Manage Nicknames')
			if "manage_messages" in perms and 'True' in str(perms[1]):
				permission.append('Manage Message')
			if "kick_members" in perms and 'True' in str(perms[1]):
				permission.append('Kick Members')
			if "ban_members" in perms and 'True' in str(perms[1]):
				permission.append('Ban Members')
			if "manage_roles" in perms and 'True' in str(perms[1]):
				permission.append('Manage Roles')
			if "mention_everyone" in perms and 'True' in str(perms[1]):
				permission.append('Mention Everyone')
			if "manage_channels" in perms and 'True' in str(perms[1]):
				permission.append('Manage Channels')

		if roles == []:
			roles.append('@everyone')
			no_of_roles = 1

		roles = roles[::-1]
		roles = ' '.join(roles)
		permission = ', '.join(permission)


		embed = discord.Embed(
			description = user.mention,
			timestamp = ctx.message.created_at, 
			colour = discord.Color.blue()
		)
		embed.set_author(name= user, url=user.avatar_url, icon_url=user.avatar_url)
		embed.add_field(name= "**Joined**", value = joined_at  , inline = True)
		embed.add_field(name= "**Registered**", value = created_at  , inline = True)
		embed.add_field(name= f"**Roles**[{no_of_roles}]", value = roles  , inline = False)
		embed.add_field(name= "**Permissions**", value = permission  , inline = False)
		embed.set_thumbnail(url=user.avatar_url)
		embed.set_footer(text = f"ID: {user.id}")
		await ctx.send(embed=embed)

	@commands.command(aliases = ['av'])
	async def avatar(self, ctx, user: discord.Member = None):
		if not user:
			user = ctx.author

		embed = discord.Embed(title = 'Avatar', colour = discord.Color.blue())
		embed.set_author(name= user, url=user.avatar_url, icon_url=user.avatar_url)
		embed.set_image(url=user.avatar_url)
		embed.set_footer(text = f"Requested by {ctx.author}")

		await ctx.send(embed=embed)

	@commands.command()
	async def source(self, ctx):
		embed = discord.Embed(
			color=discord.Color.blue(),
			description="[Click Here](https://github.com/xFGhoul/RavenBot) To view my Source Code"
		)
		await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(Miscellaneous(bot))
