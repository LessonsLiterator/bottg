import asyncio
import sqlite3
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8592611518:AAHV1NS17uQGR7wAuGFUHJK-HzDnuW-ayjo"
ADMIN_IDS = [,]
CHANNEL_ID = -1003346967689  # ТВОЙ ID КАНАЛА

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080)) # Render сам подставит порт
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

# --- БАЗА ДАННЫХ ---
DB_PATH = "resumes.db"
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

# --- СОСТОЯНИЯ ---
class ResumeForm(StatesGroup):
    zelenka = State(); age = State(); exp_chat = State()
    exp_content = State(); adequacy = State(); country = State()

# --- ХЭНДЛЕРЫ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Давай заполним анкету.\n\nШаг 1: Укажи ссылку на профиль zelenka.guru")
    await state.set_state(ResumeForm.zelenka)

@dp.message(ResumeForm.zelenka)
async def process_zelenka(message: types.Message, state: FSMContext):
    if "http" not in message.text or "lolz" not in message.text and "zelenka" not in message.text:
        await message.answer("❌ Ошибка! Пришли ссылку на профиль.")
        return
    await state.update_data(zelenka=message.text)
    await message.answer("Шаг 2: Сколько тебе лет?")
    await state.set_state(ResumeForm.age)

@dp.message(ResumeForm.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Шаг 3: Опыт в чаттинге?")
    await state.set_state(ResumeForm.exp_chat)

@dp.message(ResumeForm.exp_chat)
async def process_exp_chat(message: types.Message, state: FSMContext):
    await state.update_data(exp_chat=message.text)
    await message.answer("Шаг 4: Опыт контента (Canva, Figma, Арт и т.д.)?")
    await state.set_state(ResumeForm.exp_content)

@dp.message(ResumeForm.exp_content)
async def process_exp_content(message: types.Message, state: FSMContext):
    await state.update_data(exp_content=message.text)
    await message.answer("Шаг 5: Оценка адекватности (1-10)?")
    await state.set_state(ResumeForm.adequacy)

@dp.message(ResumeForm.adequacy)
async def process_adequacy(message: types.Message, state: FSMContext):
    await state.update_data(adequacy=message.text)
    await message.answer("Шаг 6: Страна проживания?")
    await state.set_state(ResumeForm.country)

@dp.message(ResumeForm.country)
async def process_country(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    data = await state.get_data()
    user = message.from_user
    username = f"@{user.username}" if user.username else "Нет юзернейма"
    
    admin_msg = (
        f"📩 **НОВАЯ АНКЕТА!**\n👤 Юзер: {username}\n🔗 [СВЯЗАТЬСЯ](tg://user?id={user.id})\n\n"
        f"🌐 Zelenka: {data['zelenka']}\n🎂 Возраст: {data['age']}\n💬 Опыт чата: {data['exp_chat']}\n"
        f"🎨 Опыт контента: {data['exp_content']}\n🧠 Адекватность: {data['adequacy']}\n🌍 Страна: {data['country']}"
    )

    await bot.send_message(CHANNEL_ID, admin_msg, parse_mode="Markdown")
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
        except: pass

    await message.answer("Спасибо! Анкета отправлена.")
    await state.clear()

async def main():
    init_db()
    asyncio.create_task(start_webserver()) # Запуск веб-сервера
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

