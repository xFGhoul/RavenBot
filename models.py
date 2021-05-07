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

class MoyaiBoard(Model):
    discord_id = fields.BigIntField(pk=True)
    guild = fields.ForeignKeyField('ravenbot.Guild', related_name='MoyaiBoard')
    emoji_num = fields.IntField(default=3)
    channel_id = fields.BigIntField(default=None)
    enabled = fields.BooleanField()

class Counting(Model):
    discord_id = fields.BigIntField(pk=True)
    guild = fields.ForeignKeyField('ravenbot.Guild', related_name='Counting')
    counting_channel = fields.BigIntField(null=True)
    counting_goal = fields.BigIntField(default=0, null=True)
    counting_number = fields.BigIntField(default=0, null=True)
    counting_warn_message = fields.TextField(default="Please use this channel for counting only!", null=True)
    enabled = fields.BooleanField(default=True)
    last_member_id = fields.BigIntField(null=True)
    webhook_url = fields.CharField(null=True, max_length=400)

    async def increment(self, increase_no: int = 1):
        self.counting_number = F('counting_number') + increase_no
        await self.save(update_fields=['counting_number'])
        await self.refresh_from_db(fields=['counting_number'])
        return self.counting_number

    @property
    def next_number(self):
        return self.counting_number + 1
