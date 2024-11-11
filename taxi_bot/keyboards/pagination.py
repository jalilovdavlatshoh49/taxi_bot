from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.cities import cities

cities_per_page = 10 # Шумораи шаҳрҳо дар як саҳифа (шумораи ҷуфт интихоб кунед барои ду қаторӣ)

def generate_pagination_keyboard(page, callback_prefix):
    keyboard = InlineKeyboardBuilder()
    start = page * cities_per_page
    end = min(start + cities_per_page, len(cities))  # Пешгирӣ аз индексҳои берун аз ҳудуд

    # Илова кардани тугмаҳо барои шаҳрҳо, ду тугма дар як қатор
    for i in range(start, end, 2):
        row_buttons = [
            InlineKeyboardButton(text=cities[i], callback_data=f"{callback_prefix}_city_{cities[i]}")
        ]
        if i + 1 < len(cities):
            row_buttons.append(InlineKeyboardButton(text=cities[i + 1], callback_data=f"{callback_prefix}_city_{cities[i + 1]}"))
        keyboard.row(*row_buttons)

    # Илова кардани тугмаҳои саҳифагардон (Пешина ва Баъдӣ)
    pagination_buttons = []

    if page > 0:
        pagination_buttons.append(InlineKeyboardButton(text="Пешина", callback_data=f"{callback_prefix}_page_{page - 1}"))

    if end < len(cities):
        pagination_buttons.append(InlineKeyboardButton(text="Баъдӣ", callback_data=f"{callback_prefix}_page_{page + 1}"))

    # Иҷрои тугмаҳои саҳифагардон дар як қатор
    if pagination_buttons:
        keyboard.row(*pagination_buttons)

    return keyboard.as_markup()