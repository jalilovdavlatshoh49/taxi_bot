import os
from dotenv import load_dotenv
import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.start_handler import start_router
from handlers.driver_handler import driver_router
from handlers.client_handler import client_router
from handlers.inline_menu_handler import inline_menu_router

load_dotenv()

# Танзими логгирӣ
logging.basicConfig(level=logging.INFO)

# Токени боти Telegram-и худро ворид кунед
API_TOKEN = os.getenv("API_BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # URL-ро барои webhook
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Танзими бот ва диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Создание FastAPI
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # Оғози webhook
    await bot.set_webhook(WEBHOOK_URL)
    dp.include_router(start_router)
    dp.include_router(driver_router)
    dp.include_router(client_router)
    dp.include_router(inline_menu_router)

@app.on_event("shutdown")
async def on_shutdown():
    # Удаление webhook
    await bot.delete_webhook()

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return "OK"

if __name__ == '__main__':
    import uvicorn
    # Убедитесь, что вы используете uvicorn для локального тестирования
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))