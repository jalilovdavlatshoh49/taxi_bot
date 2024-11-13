from aiogram import Bot
from aiogram.filters import Command
from aiogram.types import BotCommand

# Таъин кардани фармонҳо барои ронанда
async def set_menu_commands(bot: Bot):
    from bot_file import bot
    
    commands = [
            BotCommand(command="how_to_use_bot", description="Чи тавр истифода бурдани бот"),
            BotCommand(command="taxi_channel", description="Ба гурӯҳ обуна шавед"),
            BotCommand(command="menu", description="Меню"),
            BotCommand(command="order_a_taxi", description="Фармоиши таксӣ"),
            BotCommand(command="my_drivers", description="Ронандаи ман"),
            BotCommand(command="my_posts", description="Постҳои ман"),
            BotCommand(command="my_clients", description="Клиентҳои ман"),
            BotCommand(command="new_trip", description="Сафари нав ба қайд гирифтан"),
            BotCommand(command="account", description="Маълумотҳои шахсӣ ҳамчун ронанда"),
            BotCommand(command="client_account", description="Маълумотҳои шахсӣ ҳамчун муштарӣ")
            
       ]
    await bot.set_my_commands(commands)
    

