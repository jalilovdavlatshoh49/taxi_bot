from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from words.words import *
# Роутер барои идоракунии фармонҳо
start_router = Router()

# Функсияи /start бо истифодаи CommandStart()
@start_router.message(CommandStart())
async def on_start(message: types.Message):
    user_id = message.from_user.id

    cus_driver_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=mizoj, callback_data=f"startclient:{user_id}")],
        [InlineKeyboardButton(text=ronanda, callback_data=f"startdriver:{user_id}")],
        [InlineKeyboardButton(text="Обуна шудан ба група", url="https://t.me/ronanda_bot")],
        [InlineKeyboardButton(text="Истифодабарии бот", callback_data=f"usage_guide:{user_id}")]
    ])

    
    
    await message.answer(welcome_message, reply_markup=cus_driver_keyboard)
