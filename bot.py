import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from parser import check_feeds

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("✅ Бот работает. Новости с картинками приходят автоматически.")

@dp.message(Command("parse"))
async def parse_now(msg: types.Message):
    await msg.answer("📡 Проверяю RSS...")
    await check_feeds()
    await msg.answer("✅ Готово.")

async def bg_loop():
    while True:
        await check_feeds()
        await asyncio.sleep(1800)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(bg_loop())
    await dp.start_polling(bot)

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())