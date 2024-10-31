from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from words.words import *


# Сохтани тугмаҳо барои мизоҷ ва ронанда, ва тугмаи обуна шудан
    
    
    
reg_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Регистрация", callback_data="register_driver")],
    ])
    