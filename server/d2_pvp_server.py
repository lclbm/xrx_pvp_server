import asyncio
from tortoise import Tortoise

from typing import Union
from pydest import Pydest as Pd

from .d2_config import API_KEY


class DB():
    async def __aenter__(self):
        await Tortoise.init(db_url='sqlite://db.sqlite3',
                            modules={'models': ['models.models']})
        await Tortoise.generate_schemas()

    async def __aexit__(self, exc_type, exc, tb):
        await Tortoise.close_connections()


class API():

    pd = Pd(api_key=API_KEY)
    api = pd.api

    def __init__(self):
        pass

    async def fetch_all_charactersId(self, membershipType: int,
                                     membershipId: Union[str, int]) -> list:
        _ = await self.api.get_historical_stats_for_account(
            membershipType,
            membershipId,
        )
        characterIds = [i['characterId'] for i in _['Response']['characters']]
        return characterIds

    async def fetch_all_pvp_history(self, membershipType: int,
                                    membershipId: Union[str, int],
                                    characterId: Union[str, int]) -> list:
        '''
            获取玩家的某个角色的所有pvp战绩
        '''
        res = []
        page = 0
        while True:
            _ = await self.api.get_activity_history(membershipType,
                                                    membershipId,
                                                    characterId,
                                                    count=250,
                                                    mode=5,
                                                    page=page)
            if 'activities' not in _['Response']:
                break
            activities = _['Response']['activities']
            res.extend(activities)
            count = len(activities)
            if count < 250:
                break
            else:
                page += 1

        return res

    async def fetch_pvp_details(self, membershipType: int,
                                membershipId: Union[str, int]) -> None:
        '''
            获取玩家的生涯pvp武器击杀记录，同时存入数据库
        '''

        characterIds = await self.fetch_all_charactersId(
            membershipType, membershipId)
        tasks = [
            asyncio.create_task(
                self.fetch_all_pvp_history(membershipType, membershipId,
                                           characterId))
            for characterId in characterIds
        ]
        _ = await asyncio.gather(*tasks)
        instanceIds = [
            i['activityDetails']['instanceId'] for i in _ for i in i
        ]
        # tasks = [
        #     asyncio.create_task(self.store_detail(instanceId))
        #     for instanceId in instanceIds
        # ]
        # await asyncio.gather(*tasks)
        await self.store_detail('10043594370')

    async def store_detail(self, instanceId: Union[str, int]):
        _ = await self.api.get_post_game_carnage_report(instanceId)
        entries = _['Response']['entries']
        print(instanceId)
