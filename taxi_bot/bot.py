import os
from dotenv import load_dotenv
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import BotCommand
from handlers.start_handler import start_router
from handlers.driver_handler import driver_router
from handlers.client_handler import client_router
from handlers.inline_menu_handler import inline_menu_router
from aiogram.fsm.storage.memory import MemoryStorage
from keyboards.menu import set_menu_commands

load_dotenv()
# Танзими логгирӣ
logging.basicConfig(level=logging.INFO)

# Токени боти Telegram-и худро ворид кунед
API_TOKEN = os.getenv("API_BOT_TOKEN")

# Танзими бот ва диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

main_router = Router()
    
main_router.include_router(start_router)
main_router.include_router(driver_router)
main_router.include_router(client_router)
main_router.include_router(inline_menu_router)
    


# Функсияи асосӣ барои оғоз кардани бот
async def main():
    await set_menu_commands(bot)
    dp.include_router(main_router)
    
    # Оғози боти Telegram
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())