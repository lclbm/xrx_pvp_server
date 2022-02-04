import asyncio
import datetime

from server import DB
from models import ActivityInfo, PlayerInfo


async def test():

    async with DB() as db:
        await PlayerInfo.create(membershipType=123,
                                membershipId=345,
                                acitvityCount=34,
                                weaponData={'123': [0, 1]})

    #4611686018497181967 hzw
    #4611686018489074376 baiye


asyncio.run(test())
