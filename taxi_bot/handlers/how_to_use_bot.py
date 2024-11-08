from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

start_router = Router()

# Text for each button's information
usage_parts = {
    "how_order_taxi": """Чӣ тавр фармоиши таксӣ додан?

1. Ба бот ворид шавед.
2. Дар паҳлӯи ҷои навиштани текст тугмаи меню мавҷуд аст. Онро пахш кунед, то аз функсияҳои иловагӣ бохабар шавед.
3. Тугмаи 'Муштари' ро интихоб намоед.
4. Шаҳре, ки аз он ҷо сафарро оғоз кардан мехоҳед, интихоб кунед.
5. Шаҳре, ки мехоҳед ба он сафар кунед, интихоб кунед.
6. Пас аз ин, рӯйхати ронандаҳо бо нархи сафар ва навъи мошин барои Шумо пайдо мешавад.
7. Ронандаи дилписандатонро бо пахши тугмаи 'Интихоб' интихоб кунед.

Пас аз интихоби ронанда, ба ӯ хабар фиристода мешавад. Интизор шавед, то ронанда қабул ё рад кардани фармоиши Шуморо ба Шумо хабар диҳад.
""",
    "how_driver_list": """Чӣ тавр рӯйхати сафар барои ронанда навиштан

1. Ба бот ворид шавед.
2. Тугмаи 'Старт'-ро пахш кунед, сипас тугмаи 'Ронанда' ро интихоб намоед.
3. Барои сабти ном, бот аввал аз Шумо номатонро мепурсад — номатонро ворид намоед.
4. Баъд бот рақами телефонатонро мепурсад — рақами худро ворид кунед.
5. Бот сурати мошинро талаб мекунад — акси мошинатонро ирсол кунед.

Бо анҷом додани ин қадамҳо, Шумо сабти ном шудед ва метавонед барои сафар пост эҷод кунед.
""",
    "how_create_post": """Шарҳи тугмаҳои бот

Истифодабарии бот – Бо пахши ин тугма, Шумо ба канале ворид мешавед, ки дар он тарзи истифода бурдани ботро мефаҳмонанд.
Обуна шудан ба гурӯҳ – Ин тугма Шуморо ба гурӯҳи махсус мебарад, ки бо пайваст шудан ба он, аз хабарҳои нав дар бораи сафарҳо ва дигар эълонҳо бохабар хоҳед шуд.
Фармоиши таксӣ – Бо ин тугма Шумо метавонед таксиро интихоб кунед. Сафарро бо мошини дилписанд ва бо нархи мувофиқ фармоиш дода метавонед.
""",
}

# Function to create an inline keyboard with specified buttons
def get_keyboard(exclude_key: str = None) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton("Фармоиши таксӣ", callback_data="how_order_taxi"),
        InlineKeyboardButton("Рӯйхати ронандаҳо", callback_data="how_driver_list"),
        InlineKeyboardButton("Эҷоди пост", callback_data="how_create_post")
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[btn] for btn in buttons if btn.callback_data != exclude_key]
    )
    return keyboard

# Initial menu handler
@start_router.callback_query(lambda c: c.data == "usage_guide")
async def show_usage_guide(call: types.CallbackQuery):
    keyboard = get_keyboard()
    await call.answer(chat_id=user_id, text="Тарзи истифода бурдани бот", reply_markup=keyboard)
    await call.answer()

# Handler for each usage part button
@start_router.callback_query(F.data.in_({"how_order_taxi", "how_driver_list", "how_create_post"}))
async def show_usage_part(call: types.CallbackQuery):
    selected_part = call.data
    text = usage_parts.get(selected_part, "Маълумот дастрас нест")
    keyboard = get_keyboard(exclude_key=selected_part)
    
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()

    # Add main menu button
    menu_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton("Меню", callback_data="inline_menu")]]
    )
    await call.message.answer("Меню:", reply_markup=menu_keyboard)
