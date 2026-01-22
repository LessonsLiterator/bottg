import asyncio
import sqlite3
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web # Добавили для веб-сервера

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8592611518:AAHV1NS17uQGR7wAuGFUHJK-HzDnuW-ayjo"
ADMIN_IDS = [6954868627, 6626929387]
CHANNEL_ID = -1003346967689 # ЗАМЕНИ НА СВОЙ ID КАНАЛА

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "resumes_final.db")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ВЕБ-СЕРВЕР ДЛЯ ХОСТИНГА (чтобы не засыпал) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Порт берем из переменной окружения хостинга или 8080 по умолчанию
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- ОСТАЛЬНАЯ ЛОГИКА БОТА (init_db, хэндлеры и т.д.) ---
# ... (скопируй сюда все хэндлеры из предыдущего кода: start, process_zelenka и т.д.) ...

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       user_id INTEGER, username TEXT, zelenka TEXT, 
                       age TEXT, exp_chat TEXT, exp_content TEXT, 
                       adequacy TEXT, country TEXT)''')
    conn.commit()
    conn.close()

# --- ЗАПУСК ---
async def main():
    init_db()
    # Запускаем веб-сервер и бота одновременно
    asyncio.create_task(start_webserver())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
