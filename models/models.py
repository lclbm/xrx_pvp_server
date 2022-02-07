from tortoise.models import Model
from tortoise import fields


class ActivityInfo(Model):
    instanceId = fields.IntField(pk=True)
    referenceId = fields.IntField()
    directorActivityHash = fields.IntField()
    mode = fields.IntField()
    data = fields.JSONField()
    period = fields.DatetimeField()
    
    class meta:
        table = 'activity_info'    
    
    def __str__(self):
        return self.name


class PlayerInfo(Model):
    membershipId = fields.IntField(pk=True)
    membershipType = fields.IntField()
    acitvityCount = fields.IntField()
    weaponData = fields.JSONField()

    def __str__(self):
        return self.name
