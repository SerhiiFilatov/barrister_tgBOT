import asyncio
import asyncpg
import os
from aiohttp import web
from dotenv import load_dotenv
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from aiogram.client.default import DefaultBotProperties

from bot_dialogs import main_menu, faq, ask_a_lawyer, book_a_consultation
from bot_handlers import start_exit_menu, get_information_and_stat, admin_menu
from bot_middlewares.reg_middleware import DbSessionMiddleware

load_dotenv()

WEBAPP_PORT = int(os.getenv("PORT", 8080))
WEBAPP_HOST = "0.0.0.0"

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
if not WEBHOOK_HOST:
    raise EnvironmentError("WEBHOOK_HOST environment variable is not set. Cannot set up webhook.")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

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

async def create_pool():
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        return await asyncpg.create_pool(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DATABASE')
        )

    parsed_url = urlparse(database_url)

    return await asyncpg.create_pool(
        user=parsed_url.username,
        password=parsed_url.password,
        host=parsed_url.hostname,
        port=parsed_url.port,
        database=parsed_url.path[1:]
    )

async def handle_webhook(request: web.Request):
    try:
        update = await request.json()
        asyncio.create_task(dp.feed_webhook_update(bot, update))
    except Exception as e:
        return web.Response(status=500, text="Internal Server Error")
    return web.Response(status=200, text="OK")

async def on_startup(app: web.Application):
    pool_connect = await create_pool()
    dp.update.middleware.register(DbSessionMiddleware(pool_connect))
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await dp.storage.close()
    await bot.session.close()

def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == '__main__':
    main()
