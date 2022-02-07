import asyncio
import datetime
import logging

from server import DB, API
from models import ActivityInfo, PlayerInfo

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
logging.basicConfig(level=logging.INFO)

from asyncio import Semaphore


async def test():
    async with DB():
        api = API()
        start_time = datetime.datetime.now()
        await api.fetch_pvp_details(3,4611686018489074376)
        end_time = datetime.datetime.now()
        seconds = (end_time - start_time).total_seconds()
        logging.info(f'total {seconds} seconds')

    #4611686018497181967 hzw
    #4611686018489074376 baiye



asyncio.run(test())
