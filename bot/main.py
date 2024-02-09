import asyncio
import logging
from aiogram import Dispatcher, Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import sqlite3
from environs import Env

from handlers import admins, users

# import env config file

env = Env()
env.read_env()#'../.env', recurse=False)

async def main():    
    bot = Bot(token=env("BOT_TOKEN"), parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage(), admins_set=get_admins())
    dp.include_routers(admins.router, users.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def get_admins():
    try:
        admins_set = set()
        connection = sqlite3.connect('seller_bot.db')
        cursor = connection.cursor()        
        # Проверяем наличие пользователя
        cursor.execute('SELECT user_id FROM users WHERE isadmin = 1')
        admins = cursor.fetchall()
        admins = [item[0] for item in admins]
        admins_set |= set(admins)
    except sqlite3.Error as error:
        logging.info("Ошибка при работе с SQLite", error)
        admins_set = set()
    finally:
        if connection:
            connection.close()
            logging.info(f"Список админов выгружен. {admins_set} Соединение с SQLite закрыто")
        return admins_set

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
