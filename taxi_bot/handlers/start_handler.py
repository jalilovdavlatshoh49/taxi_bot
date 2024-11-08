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
async def show_help(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фармоиши таксӣ", callback_data="how_order_taxi")],
        [InlineKeyboardButton(text="Регистратсияи ронанда", callback_data="how_driver_list")],
        [InlineKeyboardButton(text="Чи тавр пост навистан", callback_data="how_create_post")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_des_menu")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await call.message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)

# Ҳар як функсия барои нишон додани иттилооти дахлдор
@start_router.callback_query(lambda c: c.data == "how_order_taxi")
async def order_taxi_info(callback_query: CallbackQuery):
    text = (
        "Чӣ тавр фармоиши таксӣ додан:\n\n"
                  "1. Тугмаи 'Фармоиши таксӣ'-ро пахш намоед.\n\n"
                  "2. Бот аз шумо мепурсад, ки аз кадом шаҳр сафаро оғоз мекунед. Шаҳре, ки аз онҷо сафаро оғоз мекунед, бо истифодаи тугмаро интихоб кунед.\n\n"
                  "3. Бот аз шумо мепурсад, ки ба кадом шаҳр сафар мекунед. Шаҳре, ки ба он сафар мекунед, бо истифодаи тугмаро интихоб кунед.\n\n"
                  "4. Пас аз ин, рӯйхати ронандаҳо бо нархи сафар ва навъи мошин барои Шумо пайдо мешавад.\n\n"
                  "5. Ронандаи дилписандатонро бо пахши тугмаи 'Интихоб' интихоб кунед.\n\n"
                  "Пас аз интихоби ронанда, ба ӯ хабар фиристода мешавад. Интизор шавед, то ронанда қабул ё рад кардани фармоиши Шуморо ба Шумо хабар диҳад.\n\n"
                  "Эзоҳ: Дар меню функсияҳои иловагӣ барои истифодаи бот мавҷуданд, ки бо онҳо Шумо метавонед аз имкониятҳои пурраи бот баҳра баред.",
    )
    await callback_query.message.edit_text(text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Регистратсияиронанда", callback_data="how_driver_list")],
        [InlineKeyboardButton(text="Чи тавр пост навистан", callback_data="how_create_post")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_des_menu")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)

@start_router.callback_query(lambda c: c.data == "how_driver_list")
async def driver_list_info(callback_query: CallbackQuery):
    text = (
        "Чӣ тавр регистратсия барои ронанда кардан:\n\n"
                   "1. Барои сабти ном, бот аввал аз Шумо номатонро мепурсад — номатонро ворид намоед.\n\n"
                   "2. Баъд бот рақами телефонатонро мепурсад — рақами худро ворид кунед.\n\n"
                   "3. Бот сурати мошинро талаб мекунад — акси мошинатонро ирсол кунед.\n\n"
                   "Бо анҷом додани ин қадамҳо, Шумо сабти ном шудед ва метавонед барои сафар пост эҷод кунед.\n\n",
    
    "Чӣ тавр пост эҷод кардан:\n\n"
                   "1. Тугмаи 'Сафари нав ба қайд гирифтан'-ро пахш кунед.\n\n"
                   "2. Шаҳре ки сафарро оғоз мекунед, интихоб намоед.\n\n"
                   "3. Шаҳре ки мехоҳед ба он сафар кунед, интихоб кунед.\n\n"
                   "4. Бот нархи сафарро мепурсад — онро ворид намоед.\n\n"
                   "5. Сипас бот шумораи клиентҳоро, ки барои сафар мехоҳед, мепурсад — шумораро ворид кунед.\n\n"
                   "6. Дар охир, бот аз Шумо хоҳиши навиштани коментарияро мепурсад. Агар коментария надошта бошед, 'не' нависед, вагарна коментария дар бораи сафар нависед."
}
    )
    await callback_query.message.edit_text(text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фармоиши таксӣ", callback_data="how_order_taxi")],
        [InlineKeyboardButton(text="Чи тавр пост навистан", callback_data="how_create_post")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_des_menu")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await callback_query.message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)



@start_router.callback_query(lambda c: c.data == "how_create_post")
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
        [InlineKeyboardButton(text="Фармоиши таксӣ", callback_data="how_order_taxi")],
        [InlineKeyboardButton(text="Регистратсияиронанда", callback_data="how_driver_list")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_des_menu")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)


@start_router.callback_query(lambda c: c.data == "how_des_menu")
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
        [InlineKeyboardButton(text="Фармоиши таксӣ", callback_data="how_order_taxi")],
        [InlineKeyboardButton(text="Рӯйхати ронанда", callback_data="how_driver_list")],
        [InlineKeyboardButton(text="Шарҳи тугмаҳои бот", callback_data="how_des_menu")],
        [InlineKeyboardButton(text="Меню", callback_data="inline_menu")]
    ])
    await message.answer("Тарзи истифода бурдани бот.", reply_markup=keyboard)
