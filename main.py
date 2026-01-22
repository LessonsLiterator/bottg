import asyncio
import sqlite3
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8592611518:AAHV1NS17uQGR7wAuGFUHJK-HzDnuW-ayjo"
ADMIN_IDS = [6954868627, 6626929387]
CHANNEL_ID = -1003346967689  # ВСТАВЬ СЮДА ID КАНАЛА (с минусом и 100)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "resumes_final.db")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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

class ResumeForm(StatesGroup):
    zelenka = State()
    age = State()
    exp_chat = State()
    exp_content = State()
    adequacy = State()
    country = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Давай заполним анкету.\n\nШаг 1: Укажи ссылку на свой профиль zelenka.guru")
    await state.set_state(ResumeForm.zelenka)

@dp.message(ResumeForm.zelenka)
async def process_zelenka(message: types.Message, state: FSMContext):
    text = message.text.lower()
    if "http" not in text or not any(x in text for x in ["zelenka.guru", "lolz"]):
        await message.answer("❌ Ошибка! Пришли корректную ссылку на профиль.")
        return
    await state.update_data(zelenka=message.text)
    await message.answer("Шаг 2: Сколько тебе лет?")
    await state.set_state(ResumeForm.age)

@dp.message(ResumeForm.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Шаг 3: Какой у тебя опыт работы в сфере чаттинга?")
    await state.set_state(ResumeForm.exp_chat)

@dp.message(ResumeForm.exp_chat)
async def process_exp_chat(message: types.Message, state: FSMContext):
    await state.update_data(exp_chat=message.text)
    await message.answer("Шаг 4: Есть ли опыт создания контента (canva, figma, фотошоп, рисование и т.д.):")
    await state.set_state(ResumeForm.exp_content)

@dp.message(ResumeForm.exp_content)
async def process_exp_content(message: types.Message, state: FSMContext):
    await state.update_data(exp_content=message.text)
    await message.answer("Шаг 5: Оцени свою адекватность (от 1 до 10):")
    await state.set_state(ResumeForm.adequacy)

@dp.message(ResumeForm.adequacy)
async def process_adequacy(message: types.Message, state: FSMContext):
    await state.update_data(adequacy=message.text)
    await message.answer("Шаг 6: Из какой ты страны?")
    await state.set_state(ResumeForm.country)

@dp.message(ResumeForm.country)
async def process_country(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    data = await state.get_data()
    user = message.from_user
    username = f"@{user.username}" if user.username else "Нет юзернейма"
    
    # Сохранение в БД
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO candidates (user_id, username, zelenka, age, exp_chat, exp_content, adequacy, country) VALUES (?,?,?,?,?,?,?,?)",
                   (user.id, username, data['zelenka'], data['age'], data['exp_chat'], data['exp_content'], data['adequacy'], data['country']))
    conn.commit()
    conn.close()

    admin_msg = (
        f"📩 **НОВАЯ АНКЕТА!**\n\n👤 Юзер: {username}\n🔗 [СВЯЗАТЬСЯ](tg://user?id={user.id})\n\n"
        f"🌐 Zelenka: {data['zelenka']}\n🎂 Возраст: {data['age']}\n💬 Опыт чата: {data['exp_chat']}\n"
        f"🎨 Опыт контента: {data['exp_content']}\n🧠 Адекватность: {data['adequacy']}\n🌍 Страна: {data['country']}"
    )

    # 1. Отправка в КАНАЛ (архив)
    try:
        await bot.send_message(CHANNEL_ID, admin_msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка отправки в канал: {e}")

    # 2. Отправка АДМИНАМ (уведомление)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
        except: pass

    await message.answer("Спасибо! Твоя анкета отправлена.")
    await state.clear()

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM candidates ORDER BY id DESC LIMIT 30")
    rows = cursor.fetchall()
    conn.close()
    res = "\n".join([f"{r[0]}. {r[1]}" for r in rows]) if rows else "Пусто"
    await message.answer(f"Кандидаты:\n{res}")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())