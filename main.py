import asyncio
import asyncpg
import os
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
import uvicorn # Uvicorn - це ASGI-сервер, який використовується для запуску FastAPI

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from aiogram.client.default import DefaultBotProperties

# Завантажуємо змінні оточення.
# На Railway змінні оточення зазвичай встановлюються безпосередньо в налаштуваннях проєкту,
# але для локального тестування це може бути корисно.
# from dotenv import load_dotenv
# load_dotenv() # Розкоментуйте, якщо вам потрібно завантажити з .env локально

# --- Конфігурація оточення ---
WEBAPP_PORT = int(os.getenv("PORT", 8000)) # Змінено порт за замовчуванням на 8000, типовий для FastAPI
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
# Ваші існуючі роутери та діалоги підключаються без змін
from bot_dialogs import main_menu, faq, ask_a_lawyer, book_a_consultation
from bot_handlers import start_exit_menu, get_information_and_stat, admin_menu
from bot_middlewares.reg_middleware import DbSessionMiddleware # Ваша кастомна мідлваря

dp.include_router(admin_menu.router)
dp.include_router(start_exit_menu.router)
dp.include_router(get_information_and_stat.router)
dp.include_router(book_a_consultation.appointment_for_a_consultation_dialog)
dp.include_router(main_menu.main_menu_dialog)
dp.include_router(ask_a_lawyer.ask_lawyer_dialog)
dp.include_router(faq.faq_dialog)
setup_dialogs(dp)

# --- Ініціалізація FastAPI додатку ---
app = FastAPI()

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
            'port': int(os.getenv('DB_PORT', 5432)), # Порт PostgreSQL за замовчуванням
            'database': os.getenv('DATABASE')
        }

    # Відфільтрувати значення None, якщо деякі змінні оточення є необов'язковими
    conn_params = {k: v for k, v in conn_params.items() if v is not None}

    return await asyncpg.create_pool(**conn_params)

# --- Події життєвого циклу FastAPI (запуск та завершення) ---
# Цей декоратор позначає функцію, яка буде виконана під час запуску додатку
@app.on_event("startup")
async def on_startup():
    print("Запуск додатку...")
    pool_connect = await create_pool()
    # Зберігаємо пул з'єднань у стані додатку FastAPI, щоб він був доступний.
    # Хоча в нашому випадку middleware отримує його безпосередньо.
    app.state.db_pool = pool_connect
    dp.update.middleware.register(DbSessionMiddleware(pool_connect))

    # Встановлюємо вебхук
    print(f"Встановлення вебхука на {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)
    print("Вебхук успішно встановлено.")

# Цей декоратор позначає функцію, яка буде виконана під час завершення роботи додатку
@app.on_event("shutdown")
async def on_shutdown():
    print("Завершення роботи додатку...")
    # Видаляємо вебхук
    print("Видалення вебхука...")
    await bot.delete_webhook()
    print("Вебхук видалено.")

    # Закриваємо сховище та сесію бота
    await dp.storage.close()
    await bot.session.close()

    # Закриваємо пул з'єднань до бази даних
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        print("Закриття пулу бази даних...")
        await app.state.db_pool.close()
        print("Пул бази даних закрито.")

# --- Ендпоінт для вебхука ---
# Використовуємо декоратор @app.post для обробки POST-запитів на вказаному шляху
@app.post(WEBHOOK_PATH)
async def handle_webhook(request: Request):
    try:
        # FastAPI автоматично парсить JSON тіло запиту
        update = await request.json()
        # aiogram's feed_webhook_update може приймати словник update напряму
        asyncio.create_task(dp.feed_webhook_update(bot, update))
    except Exception as e:
        print(f"Помилка обробки вебхука: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Внутрішня помилка сервера"})
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "OK"})

# --- Головна точка входу для Uvicorn ---
# Цей блок запускає додаток FastAPI за допомогою Uvicorn, якщо скрипт запускається безпосередньо
if __name__ == "__main__":
    uvicorn.run(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

