import asyncio
import logging
from aiohttp import ClientConnectorError
from tortoise import Tortoise
from tortoise.exceptions import IntegrityError

from pyrate_limiter import Duration, Limiter, RequestRate
from retry import retry

from typing import Union
from pydest import Pydest as Pd
from pydest import API as Api

from .d2_config import API_KEY
from models import PlayerInfo, ActivityInfo


class DB():
    async def __aenter__(self):
        await Tortoise.init(db_url='sqlite://db.sqlite3',
                            modules={'models': ['models.models']})
        await Tortoise.generate_schemas()

    async def __aexit__(self, exc_type, exc, tb):
        await Tortoise.close_connections()


class API():
    _pd: Pd
    _api: Api
    connect_count = 0
    limiter = Limiter(RequestRate(20, Duration.SECOND))

    def __init__(self):
        self._pd = Pd(api_key=API_KEY, proxy='http://59.42.30.159:54245')
        self._api = self._pd.api

    async def _fetch_all_charactersId(self, membershipType: int,
                                      membershipId: Union[str, int]) -> list:
        _ = await self._api.get_historical_stats_for_account(
            membershipType,
            membershipId,
        )
        characterIds = [i['characterId'] for i in _['Response']['characters']]
        return characterIds

    async def _fetch_all_pvp_history(self, membershipType: int,
                                     membershipId: Union[str, int],
                                     characterId: Union[str, int]) -> list:
        '''
            获取玩家的某个角色的所有pvp战绩
        '''
        res = []
        page = 0
        while True:
            _ = await self._get_activity_history(membershipType,
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

        characterIds = await self._fetch_all_charactersId(
            membershipType, membershipId)
        logging.info(f'{membershipId} has {len(characterIds)} characters')
        tasks = [
            asyncio.create_task(
                self._fetch_all_pvp_history(membershipType, membershipId,
                                            characterId))
            for characterId in characterIds
        ]
        _ = await asyncio.gather(*tasks)

        instanceIds = set(
            [i['activityDetails']['instanceId'] for i in _ for i in i])

        logging.info(f'{membershipId} has {len(instanceIds)} pvp history')
        tasks = [
            asyncio.create_task(self.store_detail(instanceId))
            for instanceId in instanceIds
        ]
        await asyncio.sleep(10)
        await asyncio.gather(*tasks)

    @limiter.ratelimit("api", delay=True)
    @retry(Exception, tries=5, delay=2)
    async def _get_activity_history(self, membershipType, membershipId,
                                    characterId, count, mode, page) -> None:
        return await self._api.get_activity_history(membershipType,
                                                    membershipId, characterId,
                                                    count, mode, page)

    @limiter.ratelimit("api", delay=True)
    @retry(Exception, tries=5, delay=2)
    async def _get_post_game_carnage_report(
            self, instanceId: Union[str, int]) -> None:
        return await self._api.get_post_game_carnage_report(instanceId)

    @limiter.ratelimit("store", delay=True)
    async def store_detail(self, instanceId: Union[str, int]):
        if await ActivityInfo.exists(instanceId=instanceId):
            return

        _ = await self._get_post_game_carnage_report(instanceId)
        period = _['Response']['period']

        activityDetails = _['Response']['activityDetails']
        entries = _['Response']['entries']
        data = {}
        for i in entries:
            membershipId = i['player']['destinyUserInfo']['membershipId']
            extended = i.get('extended', {})
            weapons = extended.get('weapons', {})
            values = extended.get('values', {})
            weaponData = {
                _['referenceId']: [
                    _['values'][name]['basic']['value'] for name in
                    ['uniqueWeaponKills', 'uniqueWeaponPrecisionKills']
                ]
                for _ in weapons
            }
            killData = [
                values.get(name, {'basic': {
                    'value': 0.0
                }})['basic']['value'] for name in [
                    'weaponKillsGrenade', 'weaponKillsMelee',
                    'weaponKillsSuper', 'weaponKillsAbility'
                ]
            ]
            data[membershipId] = {
                'weaponData': weaponData,
                'killData': killData
            }

        try:
            await ActivityInfo.create(
                instanceId=activityDetails['instanceId'],
                referenceId=activityDetails['referenceId'],
                directorActivityHash=activityDetails['directorActivityHash'],
                mode=activityDetails['mode'],
                data=data,
                period=period)
            logging.info(f'{instanceId} stored')
        except IntegrityError:
            logging.info(f'{instanceId} already exists')
        except Exception as e:
            logging.error(e)
