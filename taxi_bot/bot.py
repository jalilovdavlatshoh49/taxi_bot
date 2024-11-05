
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import BotCommand
from handlers.start_handler import start_router
from handlers.driver_handler import driver_router
from handlers.client_handler import client_router
from handlers.inline_menu_handler import inline_menu_router
from aiogram.fsm.storage.memory import MemoryStorage
from keyboards.menu import set_menu_commands
from db.database import create_tables


# Танзими логгирӣ
logging.basicConfig(level=logging.INFO)


dp = Dispatcher(storage=MemoryStorage())

main_router = Router()
    



# Функсияи асосӣ барои оғоз кардани бот
async def main():
    await create_tables()
    await set_menu_commands(bot)
    main_router.include_router(start_router)
    main_router.include_router(driver_router)
    main_router.include_router(client_router)
    main_router.include_router(inline_menu_router)
    
    dp.include_router(main_router)
    
    # Оғози боти Telegram
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())