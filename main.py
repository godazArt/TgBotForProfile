import asyncio
import os

import logging
import sys

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from database.orm_query import orm_get_categories_names
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode 

from database.engine import create_db, drop_db, session_maker

from common import bot_cmds_list
from middlewares.db import DataBaseSession
from handlers.user_private import user_private_router
from handlers.admin_private import admin_router
from handlers.user_group import user_group_router



bot = Bot(token=os.getenv('TOKEN'),parse_mode=ParseMode.HTML)
bot.my_admins_list = []
dp = Dispatcher()


dp.include_router(admin_router)
dp.include_router(user_private_router)
dp.include_router(user_group_router)


async def on_startup(bot):
    run_par = False
    if run_par:
        await drop_db()    
    await create_db()


async def on_shutdown(bot):

    print('Бот умер')


async def main() -> None:
    async with session_maker() as session:
        bot_cmds_list.categories = await orm_get_categories_names(session)
    print(bot_cmds_list.categories,end='\n\n\n\n\n')
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=bot_cmds_list.private,scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main()) 