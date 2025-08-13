import asyncio
import asyncpg
import os
from urllib.parse import urlparse
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
import uvicorn

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from aiogram.client.default import DefaultBotProperties

# from dotenv import load_dotenv
# load_dotenv()

# --- Конфігурація оточення ---
WEBAPP_PORT = int(os.getenv("PORT", 8000))
WEBAPP_HOST = "0.0.0.0"

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
if not WEBHOOK_HOST:
    raise EnvironmentError("Змінна оточення WEBHOOK_HOST не встановлена. Неможливо налаштувати вебхук.")


WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise EnvironmentError("Змінна оточення BOT_TOKEN не встановлена. Неможливо ініціалізувати бота.")

# --- Ініціалізація бота та диспетчера ---
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())

# --- Реєстрація роутерів та діалогів ---
from bot_dialogs import main_menu, faq, ask_a_lawyer, book_a_consultation
from bot_handlers import start_exit_menu, get_information_and_stat, admin_menu
from bot_middlewares.reg_middleware import DbSessionMiddleware

dp.include_router(admin_menu.router)
dp.include_router(start_exit_menu.router)
dp.include_router(get_information_and_stat.router)
dp.include_router(book_a_consultation.appointment_for_a_consultation_dialog)
dp.include_router(main_menu.main_menu_dialog)
dp.include_router(ask_a_lawyer.ask_lawyer_dialog)
dp.include_router(faq.faq_dialog)
setup_dialogs(dp)

# --- Функція створення пулу з'єднань до бази даних ---
async def create_pool():
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        parsed_url = urlparse(database_url)
        conn_params = {
            'user': parsed_url.username,
            'password': parsed_url.password,
            'host': parsed_url.hostname,
            'port': parsed_url.port,
            'database': parsed_url.path[1:]
        }
    else:
        conn_params = {
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DATABASE')
        }

    conn_params = {k: v for k, v in conn_params.items() if v is not None}

    try:
        print(f"Спроба підключення до БД за адресою: {conn_params.get('host')}:{conn_params.get('port')}/{conn_params.get('database')}")
        return await asyncpg.create_pool(**conn_params)
    except Exception as e:
        print(f"Помилка при створенні пулу з'єднань до БД: {e}")
        raise # Залишаємо raise для того, щоб Railway показав помилку і не запустив додаток

# --- Lifespan події для запуску та завершення ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск додатку...")
    pool_connect = None
    try:
        pool_connect = await create_pool()
        app.state.db_pool = pool_connect
        dp.update.middleware.register(DbSessionMiddleware(pool_connect))

        if WEBHOOK_HOST:
            print(f"Встановлення вебхука на {WEBHOOK_URL}")
            await bot.set_webhook(WEBHOOK_URL)
            print("Вебхук успішно встановлено.")
        else:
            print("WEBHOOK_HOST не встановлено, вебхук не буде налаштований.")

    except Exception as e:
        print(f"Критична помилка під час запуску: {e}")

    yield

    print("Завершення роботи додатку...")
    print("Видалення вебхука...")
    await bot.delete_webhook()
    print("Вебхук видалено.")

    await dp.storage.close()
    await bot.session.close()

    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        print("Закриття пулу бази даних...")
        await app.state.db_pool.close()
        print("Пул бази даних закрито.")

# --- Ініціалізація FastAPI додатку з lifespan ---
app = FastAPI(lifespan=lifespan)

# --- Додаємо простий Health Check ендпоінт ---
@app.get("/")
async def root():
    return {"message": "Бот працює! 👋"}

# --- Ендпоінт для вебхука ---
@app.post(WEBHOOK_PATH)
async def handle_webhook(request: Request):
    try:
        update_data = await request.json()
        print(f"Отримано оновлення: {update_data}") # Логуємо отримане оновлення
        await dp.feed_webhook_update(bot, update_data)
        print("Оновлення успішно передано до диспетчера.")
    except Exception as e:
        print(f"Помилка обробки вебхука в handle_webhook: {e}")
        # Логуємо повний стек викликів для детальнішої діагностики
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Внутрішня помилка сервера"})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "OK"})

# --- Головна точка входу для Uvicorn ---
if __name__ == "__main__":
    uvicorn.run(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
