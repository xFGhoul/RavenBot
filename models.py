import asyncio


from tortoise import fields
from tortoise.models import Model


class Guild(Model):
    discord_id = fields.BigIntField(pk=True)
    blacklisted_channels = fields.BigIntField(null=True)
    prefix = fields.TextField(default='-')

class Invites(Model):
    inviter_id = fields.BigIntField(pk=True)
    guild = fields.ForeignKeyField('ravenbot.Guild', related_name='Invites')
    invite_count = fields.IntField(default=1)
