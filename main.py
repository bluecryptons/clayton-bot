import json
import time
from config.config import Config
from config.proxy_list import proxyList
from src.core.core import Core
from src.core.telegram import Telegram
from src.utils.helper import Helper
from src.utils.logger import logger
from src.utils.twist import twist


async def operation(account, proxy, user_stats, session):
    try:
        core = Core(account, proxy, user_stats, session)
        await core.login(True)
        await core.start(True)
        await core.getUserStats(True)
        await core.getTask(True)
        await core.completeTask(True)
        await core.startFarming()
        await core.getSession()

        for task in core.tasks:
            if not task['is_completed']:
                await core.completeTask(task)
            if task['is_rewarded'] and not task['is_completed']:
                await core.claimFarming(task)

        while core.daily_attempts != 0:
            await core.startPartnerTask()

        task_ids = [TaskID1, TaskID2]  # Replace with actual task IDs
        for task in core.tasks:
            if task['id'] in task_ids and not task['is_completed']:
                await core.startTask(task)
            if task['id'] in task_ids and task['is_completed'] and not task['is_rewarded']:
                await core.completeTaskTwitter(task)

        await core.disconnect()
        await core.clearInfo()
        await Helper.showLog(0xea60 * 0x3c * 0x8, account, f'User ID: {account["id"]}', core)
        await operation(account, proxy, user_stats, session)
    except Exception as e:
        twist.log(account)
        twist.clear()
        await Helper.showLog(0x2710, account, f'Error: {str(e)}')
        await operation(account, proxy, user_stats, session)


async def startBot():
    init = False
    try:
        logger.info('Starting Bot')
        telegram = Telegram()

        if not init:
            await telegram.init()
            init = True

        accounts = Helper.readQueryFile('query.txt')
        session_info = []
        if len(proxyList) > 0:
            if len(accounts) != len(proxyList):
                raise ValueError(f'You provide {len(proxyList)} Proxy but have {len(accounts)} Session')

        for account in accounts:
            account_data = Helper.readQueryFile(f'account_{account}.json')
            proxy = proxyList[account] if len(proxyList) > 0 else None

            if 'session' not in account:
                await telegram.start(f'Joining Channel: https://t.me/skeldrophunt', proxy)
                telegram.session = account
                me = await telegram.client.getMe()
                user_stats = await telegram.getUserStats()
                user_data = Helper.extractUserData(user_stats)

                await telegram.clear()
                session_info.append([me, user_stats, user_data, proxy])
            else:
                user_data = Helper.queryToJSON(account_data)
                user_data['first_name'] = user_data['first_name']
                user_data['last_name'] = user_data['last_name']
                session_info.append([user_data, account_data, user_data, proxy])

        tasks = [operation(info[0], info[1], info[2], info[3]) for info in session_info]
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error('Error during bot start', str(e))


if __name__ == "__main__":
    import asyncio

    try:
        logger.info('Bot is initializing...')
        asyncio.run(startBot())
    except Exception as e:
        twist.clear()
        logger.error('Initialization failed', str(e))
        asyncio.run(startBot())
