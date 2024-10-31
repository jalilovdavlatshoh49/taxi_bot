from aiogram import Bot
from aiogram.filters import Command
from aiogram.types import BotCommand

# Таъин кардани фармонҳо барои ронанда
async def set_menu_commands(bot: Bot):
    from bot import bot
    
    commands = [
            BotCommand(command="taxi_channel", description="Ба канал обуна шавед"),
            BotCommand(command="menu", description="Меню"),
            BotCommand(command="order_a_taxi", description="Фармоиши таксӣ"),
            BotCommand(command="my_drivers", description="Ронандаи ман"),
            BotCommand(command="client_account", description="Аккаунт барои клиент"),
            BotCommand(command="my_posts", description="Постҳои ронанда"),
            BotCommand(command="my_clients", description="Клиентҳои ронанда"),
            BotCommand(command="new_trip", description="Сафари нав ба қайд гирифтан"),
            BotCommand(command="account", description="Аккаунт барои ронанда")
            
       ]
    await bot.set_my_commands(commands)
    

