from aiogram import Router, Bot, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.pagination import generate_pagination_keyboard
from keyboards.ratings import calculate_avg_rating
# from keyboards.menu import set_client_commands
from data.cities import cities
from db.database import Driver, Client, DriverPost, ClientPost, DriverRating, CarImage, AsyncSessionLocal
from sqlalchemy import desc, select, update
from math import ceil
from states.client_states import ClientPostFSM, ClientRegistrationFSM, EditClientInfo
from keyboards.get_driver_post import build_pagination_keyboard, build_post_keyboard

# Ташкили роутер барои мизоҷ
client_router = Router()

cities_per_page = 5





# Пас аз пахш кардани тугмаи "Мизоҷ"
@client_router.callback_query(lambda call: call.data.startswith("startclient"))
async def welcome_client(call: types.CallbackQuery, state: FSMContext):
    keyboard = generate_pagination_keyboard(page=0, callback_prefix="client_from_city")
    await call.message.answer("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
    await state.set_state(ClientPostFSM.waiting_for_from_city)

        
    
    
# Хандлер барои интихоби шаҳри оғоз
@client_router.callback_query(lambda call: call.data.startswith("client_from_city"))
async def process_from_city_callback(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split("_")
    
    if "page" in data:
        page = int(data[-1])
        keyboard = generate_pagination_keyboard(page, callback_prefix="client_from_city")
        await call.message.edit_text("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
    else:
        city = data[-1]
        await state.update_data(waiting_for_client_from_city=city)
        await call.message.edit_text(f"Шумо аз шаҳри {city} сафарро оғоз мекунед:")
        
        keyboard = generate_pagination_keyboard(page=0, callback_prefix="client_to_city")
        await call.message.answer("Ба кадом шаҳр сафар мекунед?", reply_markup=keyboard)
        await state.set_state(ClientPostFSM.waiting_for_to_city)
        
        
# Хандлер барои интихоби шаҳри сафар
@client_router.callback_query(lambda call: call.data.startswith("client_to_city"))
async def process_to_city_callback(call: types.CallbackQuery, state: FSMContext):
    session = AsyncSessionLocal()
    data = call.data.split("_")
    
    if "page" in data:
        page = int(data[-1])
        keyboard = generate_pagination_keyboard(page, callback_prefix="client_to_city")
        await call.message.edit_text("Ба кадом шаҳр сафар мекунед?", reply_markup=keyboard)
    else:
        city = data[-1]
        await state.update_data(waiting_for_client_to_city=city)
        await call.message.edit_text(f"Шумо ба шаҳри {city} сафар мекунед.")
        
    
        # Гирифтани маълумотҳои ҷамъшуда
        user_data = await state.get_data()
        
        from_city = user_data['waiting_for_client_from_city']
        to_city = user_data['waiting_for_client_to_city']
            
        page = 1
         
        per_page = 5
        query_result = await session.execute(select(DriverPost).where(DriverPost.from_city == from_city, DriverPost.to_city == to_city, DriverPost.is_online == True).order_by(DriverPost.current_clients))
        query = query_result.scalars().all()
        await session.close()
        total_posts = len(query)
        posts_result = await session.execute(select(DriverPost).where(DriverPost.from_city == from_city, DriverPost.to_city == to_city, DriverPost.is_online == True).order_by(DriverPost.current_clients.desc()).offset((page - 1) * per_page).limit(per_page))
        posts = posts_result.scalars().all()
        await session.close()
        
        
        if not posts:
            await call.message.answer("Постҳои онлайн ёфт нашуданд.")
            return
        
        # Намоиши постҳо
        for post in posts:
            driver_result = await session.execute(select(Driver).where(Driver.id == post.driver_id))
            driver = driver_result.scalars().first()
            await session.close()
            post_information = (
                f"Аз: {post.from_city}\n"
                f"Ба: {post.to_city}\n\n" 
                f"Нарх: {post.price}\n\n" 
                f"Шумораи клиенти кабулкардашуда: {post.current_clients}\n\n" 
                f"Шумораи клиенти лозима: {post.max_clients}\n\n" 
                f"Номи ронанда: {driver.name}\n\n" 
                f"Телефони ронанда: {driver.phone_number}\n\n"
                f"Баҳои Ронанда аз 1 то 5: {driver.avr_rating}\n\n"
                f"Комментария:\n {post.comment if post.comment else 'ронанда коментария нагузоштааст'}\n\n"
                )

            car_images_from_db_result = await session.execute(select(CarImage).where(CarImage.driver_user_id == driver.user_id))
            car_images_from_db = car_images_from_db_result.scalars().all()
            await session.close()
            media=[]    
            for car_image in car_images_from_db:
                car_img=car_image.file_id
                media.append(InputMediaPhoto(media=car_img))
            await call.message.answer_media_group(media)
            media.clear()
            await session.close()
            
            
            await call.message.answer(
                text=post_information,
                reply_markup=build_post_keyboard(post.id)
            )
        # Илова кардани тугмаҳои навигатсия
        markup = build_pagination_keyboard(from_city, to_city, page, total_posts)
        await call.message.answer("Интихоби сахифа", reply_markup=markup)

        await state.set_state(ClientPostFSM.waiting_for_selected_post_id)

# Обработчики барои тугмаҳои пеш ва баъд
@client_router.callback_query(lambda call: call.data.startswith("driver_prev"))
async def prev_page(call: types.CallbackQuery, state: FSMContext):
    session = AsyncSessionLocal()
    data = call.data.split(":")
    from_city = data[1]
    to_city = data[2]
    page = int(data[3])
    
         
    per_page = 5
    query_result = await session.execute(select(DriverPost).where(DriverPost.from_city == from_city, DriverPost.to_city == to_city, DriverPost.is_online == True).order_by(DriverPost.current_clients))
    query = query_result.scalars().all()
    await session.close()
    total_posts = len(query)
    posts_result = await session.execute(select(DriverPost).where(DriverPost.from_city == from_city, DriverPost.to_city == to_city, DriverPost.is_online == True).order_by(DriverPost.current_clients.desc()).offset((page - 1) * per_page).limit(per_page))
    posts = posts_result.scalars().all()
    await session.close()
    # Намоиши постҳо
    for post in posts:
        driver_result = await session.execute(select(Driver).where(Driver.id == post.driver_id))
        driver = driver_result.scalars().first()
        await session.close()
        post_information = (
            f"Аз: {post.from_city}\n"
            f"Ба: {post.to_city}\n\n" 
            f"Нарх: {post.price}\n\n" 
            f"Шумораи клиенти кабулкардашуда: {post.current_clients}\n\n" 
            f"Шумораи клиенти лозима: {post.max_clients}\n\n" 
            f"Номи ронанда: {driver.name}\n\n" 
            f"Телефони ронанда: {driver.phone_number}\n\n"
            f"Баҳои Ронанда аз 1 то 5: {driver.avr_rating}\n\n"
            f"Комментария:\n {post.comment if post.comment else 'ронанда коментария нагузоштааст'}\n\n"
            )

        car_images_from_db_result = await session.execute(select(CarImage).where(CarImage.driver_user_id == driver.user_id))
        car_images_from_db = car_images_from_db_result.scalars().all()
        await session.close()
        media=[]    
        for car_image in car_images_from_db:
            car_img=car_image.file_id
            media.append(InputMediaPhoto(media=car_img))
        await call.message.answer_media_group(media)
        media.clear()
        

        await call.message.answer(
            post_information,
            reply_markup=build_post_keyboard(post.id)
            )

    
    markup = build_pagination_keyboard(from_city, to_city, page, total_posts)
    await call.message.answer(f"Саҳифаи {page}", reply_markup=markup)
    await state.set_state(ClientPostFSM.waiting_for_selected_post_id)

@client_router.callback_query(lambda call: call.data.startswith("driver_next"))
async def next_page(call: types.CallbackQuery, state: FSMContext):
    session = AsyncSessionLocal()
    data = call.data.split(":")
    from_city = data[1]
    to_city = data[2]
    page = int(data[3])
         
    per_page = 5
    query_result = await session.execute(select(DriverPost).where(DriverPost.from_city == from_city, DriverPost.to_city == to_city, DriverPost.is_online == True).order_by(DriverPost.current_clients))
    query = query_result.scalars().all()
    await session.close()
    total_posts = len(query)
    posts_result = await session.execute(select(DriverPost).where(DriverPost.from_city == from_city, DriverPost.to_city == to_city, DriverPost.is_online == True).order_by(DriverPost.current_clients.desc()).offset((page - 1) * per_page).limit(per_page))
    posts = posts_result.scalars().all()
    await session.close()
    
    
    # Намоиши постҳо
    for post in posts:
        driver_result = await session.execute(select(Driver).where(Driver.id == post.driver_id))
        driver = driver_result.scalars().first()
        await session.close()
        post_information = (
            f"Аз: {post.from_city}\n"
            f"Ба: {post.to_city}\n\n" 
            f"Нарх: {post.price}\n\n" 
            f"Шумораи клиенти кабулкардашуда: {post.current_clients}\n\n" 
            f"Шумораи клиенти лозима: {post.max_clients}\n\n" 
            f"Номи ронанда: {driver.name}\n\n" 
            f"Телефони ронанда: {driver.phone_number}\n\n"
            f"Баҳои Ронанда аз 1 то 5: {driver.avr_rating}\n"
            f"Комментария:\n {post.comment if post.comment else 'ронанда коментария нагузоштааст'}\n\n"
            )

        car_images_from_db_result = await session.execute(select(CarImage).where(CarImage.driver_user_id == driver.user_id))
        car_images_from_db = car_images_from_db_result.scalars().all()
        await session.close()
        media=[]    
        for car_image in car_images_from_db:
            car_img=car_image.file_id
            media.append(InputMediaPhoto(media=car_img))
        await call.message.answer_media_group(media)
        media.clear()
        

        await call.message.answer(
            text=post_information,
            reply_markup=build_post_keyboard(post.id)
            )

    
    markup = build_pagination_keyboard(from_city, to_city, page, total_posts)
    await call.message.answer(f"Саҳифаи {page}", reply_markup=markup)
    await state.set_state(ClientPostFSM.waiting_for_selected_post_id)




# Ҳодисаи пахши тугмаи "Интихоб"
@client_router.callback_query(lambda call: call.data.startswith("choose"))
async def handle_choose_post(call: CallbackQuery, state: FSMContext):

    # ID постро мегирем аз callback data
    post_id = int(call.data.split(":")[1])
    await state.update_data(waiting_for_selected_post_id=post_id)

    await call.message.answer("Шумо чанд нафаред?:")
    await state.set_state(ClientPostFSM.waiting_for_num_clients)

# Қабули шумораи мизоҷон ва сабти мизоҷ дар пойгоҳи додаҳо
@client_router.message(ClientPostFSM.waiting_for_num_clients)
async def process_num_clients(message: types.Message, state: FSMContext):
    await state.update_data(waiting_for_num_clients=message.text)
    from bot import bot
    session = AsyncSessionLocal()
    user_data = await state.get_data()
    post_id = user_data["waiting_for_selected_post_id"]
    num_clients = user_data['waiting_for_num_clients']

                    
    # Маълумоти мизоҷро ёфтан
    user_id = message.from_user.id

    client_result = await session.execute(select(Client).where(Client.user_id == user_id))
    client = client_result.scalars().first()
    post_result = await session.execute(select(DriverPost).where(DriverPost.id == post_id))
    post = post_result.scalars().first()
    await session.close()
    post_current_clients = post.current_clients        
    post_max_clients = post.max_clients
    if int(post_current_clients) + int(num_clients) <= int(post_max_clients):
        if client:
            # Гирифтани маълумотҳои ҷамъшуда
            user_data = await state.get_data()
            num_clients = user_data['waiting_for_num_clients']
            from_city = user_data['waiting_for_client_from_city']
            to_city = user_data['waiting_for_client_to_city']
            post_id = user_data["waiting_for_selected_post_id"]
            
            # Сабти мизоҷ ба пойгоҳи додаҳо
            new_client = ClientPost(
                num_clients=num_clients,
                from_city=from_city,
                to_city=to_city,
                selected_post_id=post_id,
                client_user_id=user_id
                )
            async with session.begin():    
                session.add(new_client)
                await session.commit()
                await session.close()
            async with session.begin():
                new_current_clients = int(post_current_clients) + int(num_clients)
                await session.execute(update(DriverPost).where(DriverPost.id == post.id).values(current_clients = new_current_clients))
                await session.commit()
                await session.close()
            
    

            state.clear()
            
            # Пост ва ронандаро аз базаи маълумот ёфтан
            post_result = await session.execute(select(DriverPost).where(DriverPost.id == post_id))
            post = post_result.scalars().first()
            driver_result = await session.execute(select(Driver).where(Driver.id == post.driver_id))
            driver = driver_result.scalars().first()
            clientpost_result = await session.execute(select(ClientPost).where(ClientPost.client_user_id == user_id).order_by(desc(ClientPost.id)))
            clientpost = clientpost_result.scalars().first()
            await session.close()
            # Паёми тасдиқ ба мизоҷ
            await message.answer(text=f"Шумо постро интихоб кардед: {post.from_city} -> {post.to_city}\n Нарх: {post.price} сомонӣ.\n Ронанда: {driver.name}.\n Телефони ронанда: {driver.phone_number} ")
            
    
        
    
            driver_message = (
                f"Клиент сафарро интихоб кард:\n"
                f"Шаҳр аз: {post.from_city} Ба: {post.to_city}\n\n"
                f"Нарх: {post.price} сомонӣ\n\n"
                f"Клиент: {client.name}\n\n"
                f"Телефон: {client.phone_number}\n\n"
                f"Шумораи клиент: {clientpost.num_clients}\n\n"
                "Клиент занги шуморо интизор аст. Бо клиент сӯҳбат кунед ва ӯро қабул кунед."
            )
        
            # Эҷоди тугмаҳои қабул ва рад
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Қабул кардан", callback_data=f"accept_{client.id}_{post.id}")],
                [InlineKeyboardButton(text="Рад кардан", callback_data=f"decline_{client.id}_{post.id}")]
            ])

            try:
                await bot.send_message(
                    chat_id=driver.user_id,  # ID-и Telegram-и ронанда
                    text=driver_message,
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Хатогӣ ҳангоми фиристодани паём ба ронанда: {e}")



        else:
            
            client_registration_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="регистратсия", callback_data="client_registration")],
                ])

            await message.answer("Лутфан регистратсия кунед", reply_markup=client_registration_keyboard)

    else:
        keyboard = generate_pagination_keyboard(page=0, callback_prefix="client_from_city")
        await message.answer(f"Ин такси барои {num_clients} нафар чои холӣ надорад.\n\n Лутфан дигар таксиро заказ кунед.\n\n Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
        await state.set_state(ClientPostFSM.waiting_for_from_city)



    
@client_router.callback_query(lambda call: call.data=="client_registration")
async def client_registration(call: CallbackQuery, state: FSMContext):
    
    await call.message.answer("Лутфан номатонро нависед:")
    await state.set_state(ClientRegistrationFSM.waiting_for_name)



    
# Қабули номи мизоҷ ва талаб кардани рақами телефон
@client_router.message(ClientRegistrationFSM.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(waiting_for_name=message.text)
    await message.answer("Лутфан рақами телефони худро нависед:")
    await state.set_state(ClientRegistrationFSM.waiting_for_phone_number)

# Қабули рақами телефон ва талаб кардани шумораи мизоҷон
@client_router.message(ClientRegistrationFSM.waiting_for_phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    await state.update_data(waiting_for_phone_number=message.text)
        
    from bot import bot
    

    # Маълумоти мизоҷро ёфтан
    user_id = message.from_user.id
 
    # Гирифтани маълумотҳои ҷамъшуда
    user_data = await state.get_data()
    name = user_data['waiting_for_name']
    phone_number = user_data['waiting_for_phone_number']
    
    # Сабти мизоҷ ба пойгоҳи додаҳо
    new_client = Client(
        name=name,
        phone_number=phone_number,
        user_id=user_id
        )
    async with AsyncSessionLocal() as session:    
        async with session.begin():
            session.add(new_client)
            await session.commit()
            await session.close()           
    

    state.clear()
    async with AsyncSessionLocal() as session:    
        client_result = await session.execute(select(Client).where(Client.user_id == user_id))
        client = client_result.scalars().first()
        clientpost_result = await session.execute(select(ClientPost).where(ClientPost.client_user_id == client.user_id).order_by(desc(ClientPost.id)))
        clientpost = clientpost_result.scalars().first()
        post_id = clientpost.id
        post_result = await session.execute(select(DriverPost).where(DriverPost.id == post_id))
        post = post_result.scalars().first()
        driver_result = await session.execute(select(Driver).where(Driver.id == post.driver_id))
        driver = driver_result.scalars().first()
        await session.close()
        if clientpost:    
     
            # Паёми тасдиқ ба мизоҷ
            await message.answer(text=f"Шумо постро интихоб кардед: {post.from_city} -> {post.to_city}\n Нарх: {post.price} сомонӣ.\n Ронанда: {driver.name}.\n Телефони ронанда: {driver.phone_number} ")
            
    
        
    
            driver_message = (
                f"Клиент сафарро интихоб кард:\n"
                f"Шаҳр аз: {post.from_city} Ба: {post.to_city}\n\n"
                f"Нарх: {post.price} сомонӣ\n\n"
                f"Клиент: {client.name}\n\n"
                f"Телефон: {client.phone_number}\n\n"
                f"Шумораи клиент: {clientpost.num_clients}\n\n"
                "Клиент занги шуморо интизор аст. Бо клиент сӯҳбат кунед ва ӯро қабул кунед."
            )
            
            # Эҷоди тугмаҳои қабул ва рад
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Қабул кардан", callback_data=f"accept_{client.id}_{post.id}")],
                [InlineKeyboardButton(text="Рад кардан", callback_data=f"decline_{client.id}_{post.id}")]
            ])

            try:
                await bot.send_message(
                    chat_id=driver.user_id,  # ID-и Telegram-и ронанда
                    text=driver_message,
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Хатогӣ ҳангоми фиристодани паём ба ронанда: {e}")
            



 
@client_router.callback_query(lambda call: call.data.startswith("another_taxi"))
async def choose_another_taxi(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split(":")
    clientpost_id = int(data[1])
    session = AsyncSessionLocal()
    clientpost_result = await session.execute(select(ClientPost).where(ClientPost.id == clientpost_id))
    clientpost = clientpost_result.scalars().first()
    await session.close()
    if clientpost:
        async with session.begin():
            await session.delete(clientpost)
            await session.commit()
            await session.close()
    keyboard = generate_pagination_keyboard(page=0, callback_prefix="client_from_city")
    await call.message.answer("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
    await state.set_state(ClientPostFSM.waiting_for_from_city)




# Функсия барои қабул кардани баҳо аз тугмаҳо
@client_router.callback_query(lambda call: call.data.startswith("rate"))
async def process_rating(call: CallbackQuery):
    from bot import bot
    client_user_id=call.from_user.id
    # Парс кардани callback_data
    data=call.data.split(":")
    driver_id=data[1] 
    rating_value=data[2] 
    trip_id = data[3]
    driver_id = int(driver_id)
    rating_value = int(rating_value)
    trip_id = int(trip_id)

    session = AsyncSessionLocal()
    driver_result = await session.execute(select(Driver).where(Driver.id == driver_id))
    driver = driver_result.scalars().first()
    client_result = await session.execute(select(Client).where(Client.user_id == client_user_id))
    client = client_result.scalars().first()
    await session.close()    
    async with session.begin():
        new_rating = DriverRating(driver_id=driver.id, client_id=client.id, rating=rating_value)
        session.add(new_rating)
        await session.commit()
        await session.close()
    # Ҳисоб кардани баҳои миёнаи ронанда
    avg_rating = await calculate_avg_rating(driver.id)
    async with session.begin():
        await session.execute(update(Driver).where(Driver.id == driver_id).values(avr_rating = avg_rating))
        await session.commit()
        await session.close()
    # Паёми тасдиқ барои клиент
    await call.message.answer(f"Шумо ба ронандаи {driver.name} баҳои {rating_value} гузоштед.\n ")

    # Фиристодани паёми тасдиқ барои ронанда
    await bot.send_message(driver.user_id, f"Баҳои нав аз сафар: {rating_value}.")

@client_router.message(Command("my_drivers"))
async def my_posts(message: types.Message, state: FSMContext):
    session = AsyncSessionLocal()
    user_id = message.from_user.id
    
    clientposts_result = await session.execute(select(ClientPost).where(ClientPost.client_user_id == user_id))
    clientposts = clientposts_result.scalars().all()
    await session.close()
    if clientposts:
        for clientpost in clientposts:
            driverpost_result = await session.execute(select(DriverPost).where(DriverPost.id == clientpost.selected_post_id))
            driverpost = driverpost_result.scalars().first()
            driver_result = await session.execute(select(Driver).where(Driver.id == driverpost.driver_id))
            driver = driver_result.scalars().first()
            await session.close()
            driver_info = (
                    f"Маълумот дар бораи сафар:\n\n"
                f"Аз шаҳри: {driverpost.from_city}\n\n"
                f"Ба шаҳри: {driverpost.to_city}\n\n"
                f"Нарх: {driverpost.price}\n\n"
                f"Шумораи клиенти кабулкардашуда: {driverpost.current_clients}\n\n"
                f"Шумораи клиенти лозима: {driverpost.max_clients}\n\n"
                f"Номи ронанда: {driver.name}\n\n" 
                f"Телефони ронанда: {driver.phone_number}\n\n"
                f"Баҳои Ронанда аз 1 то 5: {driver.avr_rating}\n\n"
                f"Комментария:\n {driverpost.comment if driverpost.comment else 'ронанда коментария нагузоштааст'}\n\n"
                )


            # Эҷоди тугмаҳои қабул ва рад
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Рад кардан", callback_data=f"declinedriver_{driver.id}_{driverpost.id}")]
            ])
            
            car_images_from_db_result = await  session.execute(select(CarImage).where(CarImage.driver_user_id == driver.user_id))
            car_images_from_db = car_images_from_db_result.scalars().all()
            await session.close()
            media=[]    
            for car_image in car_images_from_db:
                car_img=car_image.file_id
                media.append(InputMediaPhoto(media=car_img))
            await message.answer_media_group(media)
            media.clear()
               



            await message.answer(text=driver_info, reply_markup=keyboard)
                
    else:
        await message.answer("Шумо ҳанӯз такси заказ накардаед.")
        keyboard = generate_pagination_keyboard(page=0, callback_prefix="client_from_city")
        await message.answer("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
        await state.set_state(ClientPostFSM.waiting_for_from_city)


@client_router.message(Command("client_account"))
async def account_info(message: types.Message, state: FSMContext):
    session = AsyncSessionLocal()
    user_id = message.from_user.id
    client_result = await session.execute(select(Client).where(Client.user_id == user_id))
    client = client_result.scalars().first()
    await session.close()
    if client:
        confirmation_text = (
            f"Аккаунти шумо:\n\n"
            f"Ном: {client.name}\n"
            f"Рақами телефон: {client.phone_number}\n"
            )


        # Тугма барои тасдиқ ё ивази маълумотҳо
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Ивази аккаунт", callback_data="edit_client_account")]
        ])
        await message.answer(confirmation_text, reply_markup=markup)
    else:
        client_registration_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="регистратсия", callback_data="client_registration")],
                ])

        await message.answer("Ҳануз барои заказ кардани таксӣ аккаунт надоред.\n\n Лутфан регистратсия кунед", reply_markup=client_registration_keyboard)


@client_router.message(Command("order_a_taxi"))
async def order_a_taxi(message: types.Message, state: FSMContext):
    keyboard = generate_pagination_keyboard(page=0, callback_prefix="client_from_city")
    await message.answer("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
    await state.set_state(ClientPostFSM.waiting_for_from_city)



# 6. Ивази маълумотҳо
@client_router.callback_query(lambda call: call.data == "edit_client_account")
async def edit_client_info(call: types.CallbackQuery):


    # Сохтани инлайн-клавиатура барои интихоб кардани майдон
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ном", callback_data="clientedit_name")],
        [InlineKeyboardButton(text="Рақами телефон", callback_data="clientedit_phone")],
        ])

    await call.message.answer("Чиро тағйир додан мехоҳед?", reply_markup=keyboard)

# Қабули callback-и инлайн-клавиатура ва сабти он
@client_router.callback_query(lambda call: call.data.startswith("clientedit_"))
async def choose_client_field(call: types.CallbackQuery, state: FSMContext):
    field = call.data.split("_")[1]

    await state.update_data(field=field)

    if field == "name":
        await call.message.answer("Номи навро ворид кунед:")
        await state.set_state(EditClientInfo.waiting_for_new_value)
    
    elif field == "phone":
        await call.message.answer("Рақами телефони навро ворид кунед:")
        await state.set_state(EditClientInfo.waiting_for_new_value)
    
    await call.answer()  # Ҷавоб ба callback барои пешгирӣ кардани пайғомҳои 'callback query answer timeout'

# Қабули маълумоти нав ва навсозии база
@client_router.message(EditClientInfo.waiting_for_new_value)
async def update_info(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()
    field = user_data.get("field")

    session = AsyncSessionLocal()
    client_result = await session.execute(select(Client).where(Client.user_id == user_id))
    client = client_result.scalars().first()
    await session.close()
    if field == "name":
        async with session.begin():
            await session.execute(update(Client).where(Client.user_id == user_id).values(name = message.text))
            await session.commit()
            await session.close()
            await state.clear()
    elif field == "phone":
        async with session.begin():
            await session.execute(update(Client).where(Client.user_id == user_id).values(phone_number = message.text))
            await session.commit()
            await session.close()    
            await state.clear()    
    await message.answer("Маълумотҳоятон бомуваффақият тағйир дода шуданд.")
    

@client_router.callback_query(lambda call: call.data.startswith("declinedriver"))
async def decline_driver(call: types.CallbackQuery):
    from bot import bot
    session = AsyncSessionLocal()
    user_id = call.message.from_user.id

    data = call.data.split("_")
    driver_id = int(data[1])
    post_id = int(data[2])
    
    # Гирифтани мизоҷ ва пост аз базаи маълумот
    client_result = await session.execute(select(Client).where(user_id == user_id))
    client = client_result.scalars().first()
    post_result = await session.execute(select(DriverPost).where(DriverPost.id == post_id))
    post = post_result.scalars().first()
    driver_result = await session.execute(select(Driver).where(Driver.id == post.driver_id))
    driver = driver_result.scalars().first()
    clientpost_result = await session.execute(select(ClientPost).where(ClientPost.selected_post_id == post_id))
    clientpost = clientpost_result.scalars().all()
    await session.close()
    for clientpst in clientpost:
        async with session.begin():
            new_current_clients = int(post.current_clients) - int(clientpst.num_clients)
            await session.execute(update(DriverPost).where(DriverPost.id == post.id).values(current_clients = new_current_clients))
            await session.commit()
        async with session.begin():
            await session.delete(clientpst)
            await session.commit()
            await session.close()        
        # Фиристодани паём ба ронанда
        await bot.send_message(
            chat_id=client.user_id,
            text=f"Шумо {driver.name}-ро рад кардед."
        )


        
        # Фиристодани паём ба мизоҷ
        await bot.send_message(
            chat_id=driver.user_id,
            text=f"Клиент: {client.name}\n\n Аз {post.from_city}\n ба {post.to_city}\n шуморо радъ накард.\n\n",
        )

        # Ҷавоби callback_query-ро медиҳем
        await call.answer()
