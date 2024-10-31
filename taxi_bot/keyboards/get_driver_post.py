from db.database import AsyncSessionLocal, DriverPost
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select


# Функсия барои сохтани тугмаҳои навигатсия
def build_pagination_keyboard(from_city: str, to_city: str, page: int, total_posts: int, per_page: int = 5):
    builder = InlineKeyboardBuilder()
    
    if (page - 1) * per_page > 0:
        builder.button(text="Пеш", callback_data=f"driver_prev:{from_city}:{to_city}:{page - 1}")
    
    if page * per_page < total_posts:
        builder.button(text="Баъд", callback_data=f"driver_next:{from_city}:{to_city}:{page + 1}")
    
    return builder.as_markup()
    
    
    
# Функсия барои сохтани тугмаи "Интихоб" барои ҳар як пост
def build_post_keyboard(post_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Интихоб", callback_data=f"choose:{post_id}")
    return builder.as_markup()


