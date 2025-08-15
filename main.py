import asyncio
from urllib.parse import urlparse

import asyncpg
import os
from dotenv import load_dotenv


from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from aiogram.client.default import DefaultBotProperties

from bot_dialogs import main_menu, faq, ask_a_lawyer, book_a_consultation
from bot_handlers import start_exit_menu, get_information_and_stat, admin_menu
from bot_middlewares.reg_middleware import DbSessionMiddleware

load_dotenv()

async def create_pool():
    database_url = os.getenv("DATABASE_URL")
    parsed_url = urlparse(database_url)
    conn_params = {
        "user": parsed_url.username,
        "password": parsed_url.password,
        "host": parsed_url.hostname,
        "port": parsed_url.port,
        "database": parsed_url.path[1:]
        }
    conn_params = {k: v for k, v in conn_params.items() if v is not None}
    return await asyncpg.create_pool(**conn_params)

async def main() -> None:
    bot = Bot(
        token=os.getenv('BOT_TOKEN'),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin_menu.router)
    dp.include_router(start_exit_menu.router)
    dp.include_router(get_information_and_stat.router)

    dp.include_router(book_a_consultation.appointment_for_a_consultation_dialog)
    dp.include_router(main_menu.main_menu_dialog)
    dp.include_router(ask_a_lawyer.ask_lawyer_dialog)
    dp.include_router(faq.faq_dialog)

    setup_dialogs(dp)
    pool_connect = await create_pool()
    dp.update.middleware.register(DbSessionMiddleware(pool_connect))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

