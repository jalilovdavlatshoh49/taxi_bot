from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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
        [InlineKeyboardButton(text="Истифодабарии бот", callback_data="usage_guide")]
    ])

    
    
    await message.answer(welcome_message, reply_markup=cus_driver_keyboard)



# Менюи асосӣ барои кӯмак бо қисматҳои гуногуни иттилоот

@start_router.callback_query(lambda c: c.data == "usage_guide")
async def show_help(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фармоиши таксӣ", callback_data="how_order_taxi")],
        [InlineKeyboardButton(text="Рӯйхати ронанда", callback_data="how_driver_list")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_create_post")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)

# Ҳар як функсия барои нишон додани иттилооти дахлдор
@start_router.callback_query(lambda c: c.data == "how_order_taxi")
async def order_taxi_info(callback_query: CallbackQuery):
    text = (
        "Чӣ тавр фармоиши таксӣ додан?\n\n"
        "1. Ба бот ворид шавед.\n"
        "2. Дар паҳлӯи ҷои навиштани текст тугмаи меню мавҷуд аст. Онро пахш кунед, то аз функсияҳои иловагӣ бохабар шавед.\n"
        "3. Тугмаи 'Муштари' ро интихоб намоед.\n"
        "...\n"
        "Эзоҳ: Дар меню функсияҳои иловагӣ низ мавҷуданд."
    )
    await callback_query.message.edit_text(text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Рӯйхати ронанда", callback_data="how_driver_list")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_create_post")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)

@start_router.callback_query(lambda c: c.data == "how_driver_list")
async def driver_list_info(callback_query: CallbackQuery):
    text = (
        "Чӣ тавр рӯйхати сафар барои ронанда навиштан\n\n"
        "1. Ба бот ворид шавед.\n"
        "2. Тугмаи 'Старт'-ро пахш кунед, сипас тугмаи 'Ронанда' ро интихоб намоед.\n"
        "3. Барои сабти ном, бот аввал аз Шумо номатонро мепурсад — номатонро ворид намоед.\n"
        "...\n"
        "Эзоҳ: Дар меню функсияҳои иловагӣ низ мавҷуданд."
    )
    await callback_query.message.edit_text(text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фармоиши таксӣ", callback_data="how_order_taxi")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_create_post")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)



@start_router.callback_query(lambda c: c.data == "create_post")
async def create_post_info(callback_query: CallbackQuery):
    text = (
        "Шарҳи тугмаҳои бот\n\n"
        "Истифодабарии бот – Бо пахши ин тугма, Шумо ба канале ворид мешавед, ки дар он тарзи истифода бурдани ботро мефаҳмонанд.\n"
        "Обуна шудан ба гурӯҳ – Ин тугма Шуморо ба гурӯҳи махсус мебарад.\n"
        "Фармоиши таксӣ – Бо ин тугма Шумо метавонед таксиро интихоб кунед.\n"
        "...\n"
        "Ба роҳ баромадан – Вақте ки шумораи муштариёни лозимӣ ҷамъ шуд.\n"
    )
    await callback_query.message.edit_text(text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фармоиши таксӣ", callback_data="order_taxi")],
        [InlineKeyboardButton(text="Рӯйхати ронанда", callback_data="driver_list")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)
