import asyncio
import asyncpg
import os
from aiohttp import web
from dotenv import load_dotenv


from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import settings
from bot_dialogs import main_menu, faq, ask_a_lawyer, book_a_consultation
from bot_handlers import start_exit_menu, get_information_and_stat, admin_menu
from bot_middlewares.reg_middleware import DbSessionMiddleware

load_dotenv()

async def create_pool():
    return await asyncpg.create_pool(user=settings.db_user,
                                     password=settings.db_password,
                                     host=settings.db_host,
                                     port=settings.db_port,
                                     database=settings.database)

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


# import asyncio
# import asyncpg
# from aiohttp import web
# from aiogram import Bot, Dispatcher
# from aiogram.enums import ParseMode
# from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram_dialog import setup_dialogs
# from aiogram.client.default import DefaultBotProperties
#
# from config import settings
# from bot_dialogs import main_menu, faq, ask_a_lawyer, book_a_consultation
# from bot_handlers import start_exit_menu, get_information_and_stat, admin_menu
# from bot_middlewares.reg_middleware import DbSessionMiddleware
#
# # ---------- НАСТРОЙКИ ----------
# WEBAPP_HOST = "0.0.0.0"          # хост для запуска aiohttp
# WEBAPP_PORT = 8080               # порт!
# BASE_WEBHOOK_URL = "https://barristerwebsite-production.up.railway.app/"
# WEBHOOK_PATH = "/webhook"
# WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
#
# # ---------- СОЗДАНИЕ ОБЪЕКТОВ ----------
# bot = Bot(
#     token=settings.bot_token.get_secret_value(),
#     default=DefaultBotProperties(parse_mode=ParseMode.HTML),
# )
# dp = Dispatcher(storage=MemoryStorage())
#
#
# # ---------- РОУТЕРЫ ----------
# dp.include_router(admin_menu.router)
# dp.include_router(start_exit_menu.router)
# dp.include_router(get_information_and_stat.router)
# dp.include_router(book_a_consultation.appointment_for_a_consultation_dialog)
# dp.include_router(main_menu.main_menu_dialog)
# dp.include_router(ask_a_lawyer.ask_lawyer_dialog)
# dp.include_router(faq.faq_dialog)
# setup_dialogs(dp)
#
#
# # ---------- СОЕДИНЕНИЕ С БД ----------
# async def create_pool():
#     return await asyncpg.create_pool(
#         user=settings.db_user,
#         password=settings.db_password,
#         host=settings.db_host,
#         port=settings.db_port,
#         database=settings.database
#     )
#
#
# # ---------- ОБРАБОТЧИК ВЕБХУКА ----------
# async def handle_webhook(request: web.Request):
#     print("Получен запрос от Telegram!")
#     try:
#         update = await request.json()
#         print("JSON-тело успешно получено. Запускаю обработку...")
#
#         # Создаем задачу для обработки обновления, чтобы не блокировать основной цикл
#         asyncio.create_task(dp.feed_webhook_update(bot, update))
#
#     except Exception as e:
#         print(f"Ошибка в обработке вебхука: {e}")
#
#     # Возвращаем 200 OK немедленно, не дожидаясь завершения обработки
#     return web.Response(status=200, text="OK")
#
#
# # ---------- СТАРТ/СТОП ----------
# async def on_startup(app: web.Application):
#     """
#     Выполняется при запуске приложения aiohttp.
#     """
#     # Создаем пул соединений с БД
#     pool_connect = await create_pool()
#     # Регистрируем мидлварь с пулом
#     dp.update.middleware.register(DbSessionMiddleware(pool_connect))
#
#     # Устанавливаем вебхук
#     await bot.set_webhook(WEBHOOK_URL)
#     print(f"✅ Вебхук установлен: {WEBHOOK_URL}")
#
#
# async def on_shutdown(app: web.Application):
#     """
#     Выполняется при завершении работы приложения.
#     """
#     # Удаляем вебхук
#     await bot.delete_webhook()
#     print("🛑 Вебхук удалён")
#
#
# # ---------- ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА ----------
# def main():
#     """
#     Создает и запускает aiohttp приложение.
#     """
#     app = web.Application()
#     app.router.add_post(WEBHOOK_PATH, handle_webhook)
#
#     # Регистрируем обработчики запуска и остановки
#     app.on_startup.append(on_startup)
#     app.on_shutdown.append(on_shutdown)
#
#     # Запускаем приложение. aiohttp сам управляет циклом asyncio.
#     web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
#
#
# if __name__ == '__main__':
#     main()
