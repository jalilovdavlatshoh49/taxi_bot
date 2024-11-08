from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

start_router = Router()

# Менюи асосӣ барои кӯмак бо қисматҳои гуногуни иттилоот

@start_router.callback_query(lambda c: c.data == "usage_guide")
async def show_help(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фармоиши таксӣ", callback_data="how_order_taxi")],
        [InlineKeyboardButton(text="Рӯйхати ронанда", callback_data="how_driver_list")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_create_post")]
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
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_create_post")]
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
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_create_post")]
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