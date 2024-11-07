from bot_file import bot
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import BotCommand
from handlers.start_handler import start_router
from handlers.client_handler import start_router as client_router
from handlers.driver_handler import start_router as driver_router
from handlers.inline_menu_handler import start_router as inline_menu_router
from aiogram.fsm.storage.memory import MemoryStorage
from keyboards.menu import set_menu_commands
from db.database import create_tables


# Танзими логгирӣ
logging.basicConfig(level=logging.INFO)


dp = Dispatcher(storage=MemoryStorage())


# Функсияи асосӣ барои оғоз кардани бот
async def main():
    await create_tables()
    await set_menu_commands(bot)
    
    dp.include_router(start_router)
    dp.include_router(client_router)
    dp.include_router(driver_router)
    dp.include_router(inline_menu_router)
    
    # Оғози боти Telegram
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
