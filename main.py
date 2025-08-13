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

# from config import settings
from bot_dialogs import main_menu, faq, ask_a_lawyer, book_a_consultation
from bot_handlers import start_exit_menu, get_information_and_stat, admin_menu
from bot_middlewares.reg_middleware import DbSessionMiddleware

load_dotenv()

# async def create_pool():
#     return await asyncpg.create_pool(user=os.getenv('DB_USER'),
#                                      password=os.getenv('DB_PASSWORD'),
#                                      host=os.getenv('DB_HOST'),
#                                      port=os.getenv('DB_PORT'),
#                                      database=os.getenv('DATABASE'))
# #
# async def main() -> None:
#     bot = Bot(
#         token=os.getenv('BOT_TOKEN'),
#         default=DefaultBotProperties(parse_mode=ParseMode.HTML),
#     )
#     dp = Dispatcher(storage=MemoryStorage())
#
#     dp.include_router(admin_menu.router)
#     dp.include_router(start_exit_menu.router)
#     dp.include_router(get_information_and_stat.router)
#
#     dp.include_router(book_a_consultation.appointment_for_a_consultation_dialog)
#     dp.include_router(main_menu.main_menu_dialog)
#     dp.include_router(ask_a_lawyer.ask_lawyer_dialog)
#     dp.include_router(faq.faq_dialog)
#
#     setup_dialogs(dp)
#     pool_connect = await create_pool()
#     dp.update.middleware.register(DbSessionMiddleware(pool_connect))
#
#     await bot.delete_webhook(drop_pending_updates=True)
#     await dp.start_polling(bot)
#
#
# if __name__ == '__main__':
#     asyncio.run(main())


import asyncio
import asyncpg
import os
from aiohttp import web
from dotenv import \
    load_dotenv  # load_dotenv() полезен для локальной разработки, на Railway переменные задаются напрямую
from urllib.parse import urlparse  # Для парсинга DATABASE_URL

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from aiogram.client.default import DefaultBotProperties
# from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application # Не используется, если вы делаете свой handle_webhook

# Импорт ваших роутеров и диалогов
from bot_dialogs import main_menu, faq, ask_a_lawyer, book_a_consultation
from bot_handlers import start_exit_menu, get_information_and_stat, admin_menu
from bot_middlewares.reg_middleware import DbSessionMiddleware

# Загружаем переменные окружения.
# На Railway они будут автоматически доступны, этот вызов нужен для локальной разработки.
load_dotenv()

# ---------- НАСТРОЙКИ ----------
# Порт для запуска aiohttp берется из переменной окружения PORT, которую предоставляет Railway.
# Если PORT не задан (например, при локальном запуске без .env), используется 8080.
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# Хост для запуска aiohttp. Для деплоя всегда используйте '0.0.0.0'
WEBAPP_HOST = "0.0.0.0"

# Базовый URL для вебхука берется из переменной окружения WEBHOOK_HOST (или RAILWAY_PUBLIC_DOMAIN, если вы ее так настроили).
# Это должен быть публичный домен вашего сервиса на Railway.
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
if not WEBHOOK_HOST:
    # Важно: если WEBHOOK_HOST не установлен, бот не сможет установить вебхук.
    # Для Railway это критично.
    print("Внимание: Переменная окружения WEBHOOK_HOST не установлена! Вебхук может быть не установлен.")
    # Можно установить заглушку или вызвать ошибку, в зависимости от логики.
    # Например, если вы тестируете локально без публичного URL:
    # BASE_WEBHOOK_URL = f"http://localhost:{WEBAPP_PORT}"
    # В реальном деплое на Railway WEBHOOK_HOST должен быть установлен.
    raise EnvironmentError("WEBHOOK_HOST environment variable is not set. Cannot set up webhook.")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# ---------- СОЗДАНИЕ ОБЪЕКТОВ ----------
bot = Bot(
    token=os.getenv('BOT_TOKEN'),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())

# ---------- РОУТЕРЫ ----------
dp.include_router(admin_menu.router)
dp.include_router(start_exit_menu.router)
dp.include_router(get_information_and_stat.router)
dp.include_router(book_a_consultation.appointment_for_a_consultation_dialog)
dp.include_router(main_menu.main_menu_dialog)
dp.include_router(ask_a_lawyer.ask_lawyer_dialog)
dp.include_router(faq.faq_dialog)
setup_dialogs(dp)


# ---------- СОЕДИНЕНИЕ С БД ----------
async def create_pool():
    """
    Создает пул соединений с PostgreSQL.
    Использует DATABASE_URL, которую автоматически предоставляет Railway.
    """
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        # Если DATABASE_URL не задана (например, для локальной разработки без нее),
        # используем старые переменные DB_*.
        print("Внимание: DATABASE_URL не установлена. Используются отдельные переменные DB_*.")
        return await asyncpg.create_pool(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DATABASE')
        )

    # Парсим DATABASE_URL, чтобы извлечь все параметры подключения
    parsed_url = urlparse(database_url)

    return await asyncpg.create_pool(
        user=parsed_url.username,
        password=parsed_url.password,
        host=parsed_url.hostname,
        port=parsed_url.port,
        database=parsed_url.path[1:]  # Удаляем '/' в начале имени базы данных
    )


# ---------- ОБРАБОТЧИК ВЕБХУКА ----------
async def handle_webhook(request: web.Request):
    """
    Основной обработчик вебхуков от Telegram.
    Принимает POST-запросы и передает их в диспетчер aiogram.
    """
    # Логирование для отладки
    print("Получен запрос от Telegram!")
    try:
        # Получаем JSON-тело запроса
        update = await request.json()
        # print(f"JSON-тело успешно получено: {update}") # Может быть очень много вывода

        # Обрабатываем обновление асинхронно, не блокируя HTTP-ответ
        # dp.feed_webhook_update - это правильный метод для aiogram 3.x
        asyncio.create_task(dp.feed_webhook_update(bot, update))

    except Exception as e:
        print(f"Ошибка в обработке вебхука: {e}")
        # Возвращаем 500 Internal Server Error, если произошла критическая ошибка
        return web.Response(status=500, text="Internal Server Error")

    # Telegram ожидает ответ 200 OK в течение короткого времени.
    # Отправляем его сразу, даже если обработка обновления еще идет.
    return web.Response(status=200, text="OK")


# ---------- СТАРТ/СТОП ----------
async def on_startup(app: web.Application):
    """
    Выполняется при запуске приложения aiohttp.
    Создает пул соединений с БД и устанавливает вебхук.
    """
    # Создаем пул соединений с БД
    pool_connect = await create_pool()
    # Регистрируем мидлварь с пулом
    dp.update.middleware.register(DbSessionMiddleware(pool_connect))

    # Устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Вебхук установлен: {WEBHOOK_URL}")


async def on_shutdown(app: web.Application):
    """
    Выполняется при завершении работы приложения.
    Удаляет вебхук.
    """
    # Удаляем вебхук
    await bot.delete_webhook()
    print("🛑 Вебхук удалён")
    # Закрываем пул соединений с БД
    await dp.storage.close()
    await bot.session.close()
    print("Пул БД и сессия бота закрыты.")


# ---------- ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА ----------
def main():
    """
    Создает и запускает aiohttp приложение для обработки вебхуков.
    """
    app = web.Application()
    # Регистрируем обработчик POST-запросов по WEBHOOK_PATH
    app.router.add_post(WEBHOOK_PATH, handle_webhook)

    # Регистрируем обработчики запуска и остановки приложения
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Запускаем приложение. aiohttp сам управляет циклом asyncio.
    # WEBAPP_HOST должен быть '0.0.0.0' для деплоя, WEBAPP_PORT берется из env.
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)


if __name__ == '__main__':
    # Запускаем основную функцию
    main()
