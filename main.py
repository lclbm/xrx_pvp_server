import asyncio
import datetime
import logging



from server import DB,API
from models import ActivityInfo, PlayerInfo

logging.basicConfig(level=logging.INFO)

async def test():

    api = API()
    await api.store_detail('10043594370')
        
    #4611686018497181967 hzw
    #4611686018489074376 baiye


asyncio.run(test())
