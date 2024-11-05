from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db.database import Driver, Client, DriverPost, ClientPost, CarImage, AsyncSessionLocal
from keyboards.pagination import generate_pagination_keyboard
from data.cities import cities
from math import ceil
from states.driver_states import CarImageFSM, RegisterDriverFSM, EditDriverInfo, DriverTripFSM
from sqlalchemy import desc, select, delete, update

driver_router=Router()


# Коркарди пахши тугмаи "Ронанда"
@driver_router.callback_query(lambda call: call.data.startswith("startdriver"))
async def handle_driver_choice(call: types.CallbackQuery, state: FSMContext):
    user_id_data = call.data.split(":")
    user_id = user_id_data[1]
    session = AsyncSessionLocal()
    result = await session.execute(select(Driver).where(Driver.user_id == user_id))
    driver = result.scalars().first()
    await session.delete(result)
    await session.commit()
    await session.close()
    if driver:
        img_from_db = await session.execute(select(CarImage).where(CarImage.driver_user_id == driver.user_id))
        car_images_from_db = img_from_db.scalars().all()
        await session.close()
        if car_images_from_db:
            confirmation_text = (
                f"Аккаунти шумо:\n\n"
                f"Ном: {driver.name}\n"
                f"Рақами телефон: {driver.phone_number}\n\n"   
                f"Баҳои Ронанда аз 1 то 5: {driver.avr_rating}\n"
                )

                                    
            media=[]    
            for car_image in car_images_from_db:
                car_img = car_image.file_id
                media.append(InputMediaPhoto(media=car_img))
            await call.message.answer_media_group(media)
            media.clear()
                    
                            
            # Тугма барои тасдиқ ё ивази маълумотҳо
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Ивази аккаунт", callback_data="edit_driver_account")]
                ])
                                            

            await call.message.answer(text=confirmation_text, reply_markup=markup)


            # Намоиши матни тасдиқ ва иловаи маълумот дар бораи сафар бо тугмаи бақайдгирӣ
            trip_text = (
                "Лутфан дар бораи сафар пост нависед."
                )

            # Тугмаи "Ба қайд гирифтани сафар"
            trip_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Ба қайд гирифтани сафар", callback_data="register_trip")]
                ])

            # Намоиши матн ва тугмаҳо ба якҷоя
            await call.message.answer(trip_text, reply_markup=trip_markup)
                
        else:    
            await session.delete(driver)
            await session.commit()
                                        
            await call.message.answer("Номатонро нависед:")
            await state.set_state(RegisterDriverFSM.waiting_for_name)
                                    
    
    else:
        await call.message.answer("Номатонро нависед:")
        await state.set_state(RegisterDriverFSM.waiting_for_name)


# 2. Қабули номи ронанда
@driver_router.message(RegisterDriverFSM.waiting_for_name)
async def get_driver_name(message: types.Message, state: FSMContext):
    await state.update_data(waiting_for_driver_name=message.text)
    await message.answer("Лутфан рақами телефонро ворид кунед:")
    await state.set_state(RegisterDriverFSM.waiting_for_phone)


# 3. Қабули рақами телефон
@driver_router.message(RegisterDriverFSM.waiting_for_phone)
async def get_driver_phone(message: types.Message, state: FSMContext):
    await state.update_data(waiting_for_driver_phone=message.text)
    
    user_id = message.from_user.id    
    session = AsyncSessionLocal()
    driver_data = await state.get_data()
    name=driver_data['waiting_for_driver_name']
    phone_number=driver_data['waiting_for_driver_phone']

    await state.clear()
    # Сабти маълумот ба пойгоҳи додаҳо
    async with session.begin():
        new_driver = Driver(name=name, phone_number=phone_number, user_id=user_id)

        session.add(new_driver)
        await session.commit()
        
    driver_result = await session.execute(select(Driver).where(Driver.user_id == user_id))
    driver = driver_result.scalars().first()
    await session.close()
        
    if driver:
        await message.answer("Суратҳои мошинатонро ирсол намоед:")
        await state.set_state(CarImageFSM.waiting_for_car_image)
        


# 4. Қабули сурат (URL ё пайванди сурат)
@driver_router.message(CarImageFSM.waiting_for_car_image)
async def get_car_image(message: types.Message, state: FSMContext):
    if message.photo:
        car_image = message.photo[-1].file_id

        car_img_data = await state.get_data()
        
        car_images=car_img_data.get('photos', [])
        car_images.append(car_image)
        await state.update_data(photos=car_images)
        

        done_car_image_keyboard=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Тамом", callback_data="done_car_image")]
        ])
        await message.answer("Сурат қабул шуд. Шумо метавонед суратҳои бештар ирсол кунед ё тугмаи 'тамом'-ро пахш намоед.", reply_markup=done_car_image_keyboard)
        await state.set_state(CarImageFSM.waiting_for_car_image)
    else:
        await message.answer("Лутфан сурати мошин ирсол намоед:")
        await state.set_state(CarImageFSM.waiting_for_car_image)


@driver_router.callback_query(lambda call: call.data == "done_car_image")
async def finish_image_upload(call: types.CallbackQuery, state: FSMContext):
    session = AsyncSessionLocal()
    
    user_id = call.from_user.id
    
    car_img_data=await state.get_data()
    car_images=car_img_data.get('photos', [])

    
    async with session.begin():
        for car_img in car_images:
            new_car_image = CarImage(file_id=car_img, driver_user_id=user_id)
            session.add(new_car_image)
        await session.commit()
        await session.close()
    await state.clear()

    driver_result = await session.execute(select(Driver).where(Driver.user_id == user_id))
    driver = driver_result.scalars().first()
    await session.close()
    await call.message.answer("Аккаунти шумо муваффақона сабт шуд!")
    confirmation_text = (
        f"Аккаунти шумо:\n\n"
        f"Ном: {driver.name}\n"
        f"Рақами телефон: {driver.phone_number}\n"   
        f"Баҳои Ронанда аз 1 то 5: {driver.avr_rating}\n"
        )


    car_images_from_db_result = await session.execute(select(CarImage).where(CarImage.driver_user_id == user_id))
    car_images_from_db=car_images_from_db_result.scalars().all()
    media=[]    
    for car_image in car_images_from_db:
        car_img=car_image.file_id
        media.append(InputMediaPhoto(media=car_img))
    await call.message.answer_media_group(media)
    media.clear()
    await session.close()
    # Тугма барои тасдиқ ё ивази маълумотҳо
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ивази аккаунт", callback_data="edit_driver_account")]
    ])
        
    await call.message.answer(text=confirmation_text, reply_markup=markup)
        
    # Намоиши матни тасдиқ ва иловаи маълумот дар бораи сафар бо тугмаи бақайдгирӣ
    trip_text = (
        "Лутфан дар бораи сафар пост нависед."
        )

    # Тугмаи "Ба қайд гирифтани сафар"
    trip_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ба қайд гирифтани сафар", callback_data="register_trip")]
    ])

    # Намоиши матн ва тугмаҳо ба якҷоя
    await call.message.answer(trip_text, reply_markup=trip_markup)


# 6. Ивази маълумотҳо
@driver_router.callback_query(lambda call: call.data == "edit_driver_account")
async def edit_driver_info(call: types.CallbackQuery):
    
    # Сохтани инлайн-клавиатура барои интихоб кардани майдон
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ном", callback_data="driveredit_name")],
        [InlineKeyboardButton(text="Рақами телефон", callback_data="driveredit_phone")],
        [InlineKeyboardButton(text="Сурати мошин", callback_data="driveredit_carphoto")]
    ])

    await call.message.answer(text="Чиро тағйир додан мехоҳед?", reply_markup=keyboard)

# Қабули callback-и инлайн-клавиатура ва сабти он
@driver_router.callback_query(lambda call: call.data.startswith("driveredit_"))
async def choose_field(call: types.CallbackQuery, state: FSMContext):
    field = call.data.split("_")[1]

    await state.update_data(field=field)

    if field == "name":
        await call.message.answer("Номи навро ворид кунед:")
        await state.set_state(EditDriverInfo.waiting_for_new_value)
    
    elif field == "phone":
        await call.message.answer("Рақами телефони навро ворид кунед:")
        await state.set_state(EditDriverInfo.waiting_for_new_value)
    
    elif field == "carphoto":
        await call.message.answer("Сурати нави мошинро ирсол кунед:")
        await state.set_state(EditDriverInfo.waiting_for_new_value)
    
    
# Қабули маълумоти нав ва навсозии база
@driver_router.message(EditDriverInfo.waiting_for_new_value)
async def update_info(message: types.Message, state: FSMContext):
    session = AsyncSessionLocal()
    user_id = message.from_user.id
    user_data = await state.get_data()
    field = user_data.get("field")

    if field == "name":
        # Санҷиш: ном бояд матн бошад
        name = message.text
        if not name.isalpha():  # танҳо ҳарфҳо қабул мешаванд
            await message.answer("Лутфан номи дурустро ворид намоед.")
            return
        async with session.begin():
            await session.execute(update(Driver).where(Driver.user_id == user_id).values(name=name))
            await session.commit()
        await state.clear()
        await message.answer("Маълумотҳоятон бомуваффақият тағйир дода шуданд.")
        
    elif field == "phone":
        # Санҷиш: рақами телефон бояд рақам бошад
        phone_number = message.text
        if not phone_number.isdigit():  # танҳо рақамҳо қабул мешаванд
            await message.answer("Лутфан рақами телефони дурустро ворид намоед.")
            return
        async with session.begin():
            await session.execute(update(Driver).where(Driver.user_id == user_id).values(phone_number=phone_number))
            await session.commit()
        await state.clear()
        await message.answer("Маълумотҳоятон бомуваффақият тағйир дода шуданд.")
        
    elif field == "carphoto":
        # Санҷиш: бояд аксе ирсол карда шавад
        if not message.photo:  # санҷиши акси ирсолшуда
            await message.answer("Лутфан акси дурустро ирсол намоед.")
            return
        async with session.begin():
            await session.execute(delete(CarImage).where(CarImage.driver_user_id == user_id))
            await session.commit()
        car_image = message.photo[-1].file_id

        car_img_data = await state.get_data()
        car_images = car_img_data.get('photos', [])
        car_images.append(car_image)
        await state.update_data(photos=car_images)

        done_car_image_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Тамом", callback_data="done_car_image")]
        ])
        await message.answer("Сурат қабул шуд. Шумо метавонед суратҳои бештар ирсол кунед ё тугмаи 'Тамом'-ро пахш намоед.", reply_markup=done_car_image_keyboard)
        await state.set_state(CarImageFSM.waiting_for_car_image)
        
    else:
        await message.answer("Лутфан маълумоти дуруст ворид намоед ё ирсол намоед.")
        
    

    

        
@driver_router.callback_query(lambda call: call.data == "register_trip")
async def start_trip_registration(call: CallbackQuery, state: FSMContext):
    keyboard = generate_pagination_keyboard(page=0, callback_prefix="from_city")
    await call.message.answer("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
    await state.set_state(DriverTripFSM.from_city)


# Хандлер барои интихоби шаҳри оғоз
@driver_router.callback_query(lambda call: call.data.startswith("from_city"))
async def process_from_city_callback(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split("_")
    
    if "page" in data:
        page = int(data[-1])
        keyboard = generate_pagination_keyboard(page, callback_prefix="from_city")
        await call.message.edit_text("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
    else:
        city = data[-1]
        await state.update_data(from_city=city)
        await call.message.edit_text(f"Шумо аз шаҳри {city} сафарро оғоз мекунед.")
        
        keyboard = generate_pagination_keyboard(page=0, callback_prefix="to_city")
        await call.message.answer("Ба кадом шаҳр сафар мекунед?", reply_markup=keyboard)
        await state.set_state(DriverTripFSM.to_city)

# Хандлер барои интихоби шаҳри сафар
@driver_router.callback_query(lambda call: call.data.startswith("to_city"))
async def process_to_city_callback(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split("_")
    
    if "page" in data:
        page = int(data[-1])
        keyboard = generate_pagination_keyboard(page, callback_prefix="to_city")
        await call.message.edit_text("Ба кадом шаҳр сафар мекунед?", reply_markup=keyboard)
    else:
        city = data[-1]
        await state.update_data(to_city=city)
        await call.message.edit_text(f"Шумо ба шаҳри {city} сафар мекунед.")
        
        await call.message.answer("Нархи сафарро ворид кунед:")
        await state.set_state(DriverTripFSM.price)


# Гирифтани нархи сафар
@driver_router.message(DriverTripFSM.price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("Чанд нафар клиент барои сафар лозим аст:")
        await state.set_state(DriverTripFSM.max_clients)
    except ValueError:
        await message.answer("Лутфан нархи дуруст ворид кунед (фақат рақамҳо).")

# Гирифтани шумораи мизоҷон
@driver_router.message(DriverTripFSM.max_clients)
async def process_max_clients(message: Message, state: FSMContext):
    try:
        max_clients = int(message.text)
        await state.update_data(max_clients=max_clients)
        await message.answer("Комментарияи иловагиро ворид кунед ё 'Не' нависед агар надоред:")
        await state.set_state(DriverTripFSM.comment)
    except ValueError:
        await message.answer("Лутфан як рақами дуруст ворид кунед.")

# Гирифтани комментари
@driver_router.message(DriverTripFSM.comment)
async def process_comment(message: Message, state: FSMContext):
    comment = message.text if message.text.lower() != "не" else None
    await state.update_data(comment=comment)
    user_id = message.from_user.id
    # Иҷрои баррасии маълумотҳои ҷамъшуда
    data = await state.get_data()

    session = AsyncSessionLocal()
    driver_result = await session.execute(select(Driver).where(Driver.user_id == user_id))
    driver = driver_result.scalars().first()
    await session.close()
    driver_id = driver.id
    # Иловаи маълумоти сафар ба пойгоҳи додаҳо
    new_trip = DriverPost(
        from_city=data['from_city'],
        to_city=data['to_city'],
        price=data['price'],
        max_clients=data['max_clients'],
        comment=data['comment'],
        driver_id=driver_id  # Ҳамин ронанда
    )
    async with session.begin():
        session.add(new_trip)
        await session.commit()
        await session.close()
    await message.answer("Сафари шумо бомуваффақият ба қайд гирифта шуд!")
    await state.clear()
    

    driver_trips_result = await session.execute(select(DriverPost).where(DriverPost.driver_id == driver_id).order_by(DriverPost.is_online, DriverPost.current_clients))
    driver_trips = driver_trips_result.scalars().all()
    await session.close()
    if driver_trips:
        

        for driver_trip in driver_trips:
            driver_info = (
                f"Маълумот дар бораи сафар:\n\n"
            f"Аз шаҳри: {driver_trip.from_city}\n"
            f"Ба шаҳри: {driver_trip.to_city}\n\n"
            f"Нарх: {driver_trip.price}\n"
            f"Шумораи клиенти кабулкардашуда: {driver_trip.current_clients}\n\n"
            f"Шумораи клиенти лозима: {driver_trip.max_clients}\n\n"
            f"Комментария:\n {driver_trip.comment if driver_trip.comment else 'ронанда коментария нагузоштааст'}\n\n"
            f"Пости ОФЛАЙН-ро клиент дида наметавонад.\n\n"
            f"Ин пост: {'ОНЛАЙН аст.' if driver_trip.is_online else 'ОФЛАЙН аст'}"
                )

            # Тугмаҳо барои оғози ва анҷоми ҷустуҷӯ, сафарҳои нав ва ҳазфи сафар
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Онлайн", callback_data=f"set_online:{driver_trip.id}")],
                [InlineKeyboardButton(text="Офлайн", callback_data=f"set_offline:{driver_trip.id}")],
                [InlineKeyboardButton(text="Удалить кардан", callback_data=f"delete_trip:{driver_trip.id}")],
                [InlineKeyboardButton(text="Ба роҳ баромадан", callback_data=f"start_trip:{driver_trip.id}")]
            ])


            await message.answer(driver_info, reply_markup=keyboard)
        
    else:
        await message.answer("Шумо ҳанӯз маълумотҳои худро ворид накардаед.")

    
    new_trip_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Сафари нав ба қайд гирифтан", callback_data="new_trip")],
    ])        
    await message.answer("Пост барои сафари нав нависед", reply_markup=new_trip_keyboard)


    
    
    

# Сафарро онлайн кардан
@driver_router.callback_query(lambda call: call.data.startswith("set_online"))
async def set_trip_online(call: CallbackQuery):
    session = AsyncSessionLocal()
    trip_id = int(call.data.split(":")[1])
    trip_result = await session.execute(select(DriverPost).where(DriverPost.id == trip_id))
    trip = trip_result.scalars().first()
    clientposts_result = await session.execute(select(ClientPost).where(ClientPost.selected_post_id == trip.id))
    clientposts = clientposts_result.scalars().all()
    await session.close()
    if clientposts:
        for clientpost in clientposts:
            await session.delete(clientpost)
            await session.commit()
        await session.close()    
    async with session.begin():
        await session.execute(update(DriverPost).where(DriverPost.id == trip_id).values(current_clients = int(0), is_online = True))
        await session.commit()
        await session.close()
    # Дубора гирифтани trip бо маълумоти нав
    trip_result = await session.execute(select(DriverPost).where(DriverPost.id == trip_id))
    trip = trip_result.scalars().first()

    await session.close()
    driver_info = (
            f"Маълумот дар бораи сафар:\n\n"
        f"Аз шаҳри: {trip.from_city}\n"
        f"Ба шаҳри: {trip.to_city}\n\n"
        f"Нарх: {trip.price}\n\n"
        f"Шумораи клиенти кабулкардашуда: {trip.current_clients}\n\n"
        f"Шумораи клиенти лозима: {trip.max_clients}\n"
        f"Комментария:\n {trip.comment if trip.comment else 'ронанда коментария нагузоштааст'}\n\n"
        f"Пости ОФЛАЙН-ро клиент дида наметавонад.\n\n"
        f"Ин пост: {'ОНЛАЙН аст.' if trip.is_online else 'ОФЛАЙН аст'}"
        )

    # Тугмаҳо барои оғози ва анҷоми ҷустуҷӯ, сафарҳои нав ва ҳазфи сафар
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Онлайн", callback_data=f"set_online:{trip.id}")],
    [InlineKeyboardButton(text="Офлайн", callback_data=f"set_offline:{trip.id}")],
    [InlineKeyboardButton(text="Удалить кардан", callback_data=f"delete_trip:{trip.id}")],
    [InlineKeyboardButton(text="Ба роҳ баромадан", callback_data=f"start_trip:{trip.id}")]
    ])

    await call.message.answer(driver_info, reply_markup=keyboard)
    
# Сафарро офлайн кардан
@driver_router.callback_query(lambda call: call.data.startswith("set_offline"))
async def set_trip_offline(call: CallbackQuery):
    trip_id = int(call.data.split(":")[1])
    yes_or_no_set_offline = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ҳан", callback_data=f"yesset_offline:{trip_id}")],
        [InlineKeyboardButton(text="Не", callback_data=f"noset_offline:{trip_id}")]
    ])
    await call.message.answer("Пости ОФЛАЙНРО клиент дида наметавонад.\n\n Агар клиент қабул карда бошед, ба клиентҳо хабари радъ кардани сафар мефистем.\n\n Мехоҳед ОФЛАЙН кунед?", reply_markup=yes_or_no_set_offline)

@driver_router.callback_query(lambda call: call.data.startswith("noset_offline"))
async def no_set_offline(call: CallbackQuery):
    session = AsyncSessionLocal()
    trip_id = int(call.data.split(":")[1])
    trip_result = await session.execute(select(DriverPost).where(DriverPost.id == trip_id))
    trip = trip_result.scalars().first()
    await session.close()
    
    driver_info = (
            f"Маълумот дар бораи сафар:\n\n"
        f"Аз шаҳри: {trip.from_city}\n"
        f"Ба шаҳри: {trip.to_city}\n\n"
        f"Нарх: {trip.price}\n\n"
        f"Шумораи клиенти кабулкардашуда: {trip.current_clients}\n\n"
        f"Шумораи клиенти лозима: {trip.max_clients}\n"
        f"Комментария:\n {trip.comment if trip.comment else 'ронанда коментария нагузоштааст'}\n\n"
        f"Пости ОФЛАЙН-ро клиент дида наметавонад.\n\n"
        f"Ин пост: {'ОНЛАЙН аст.' if trip.is_online else 'ОФЛАЙН аст'}"
        )

        # Тугмаҳо барои оғози ва анҷоми ҷустуҷӯ, сафарҳои нав ва ҳазфи сафар
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Онлайн", callback_data=f"set_online:{trip.id}")],
        [InlineKeyboardButton(text="Офлайн", callback_data=f"set_offline:{trip.id}")],
        [InlineKeyboardButton(text="Удалить кардан", callback_data=f"delete_trip:{trip.id}")],
        [InlineKeyboardButton(text="Ба роҳ баромадан", callback_data=f"start_trip:{trip.id}")]
        ])

    await call.message.answer(driver_info, reply_markup=keyboard)    
    



@driver_router.callback_query(lambda call: call.data.startswith("yesset_offline"))
async def yes_set_offline(call: CallbackQuery):
    from bot import bot
    session = AsyncSessionLocal()
    trip_id = int(call.data.split(":")[1])
    trip_result = await session.execute(select(DriverPost).where(DriverPost.id == trip_id))
    trip = trip_result.scalars().first()
    clientposts_result = await session.execute(select(ClientPost).where(ClientPost.selected_post_id == trip.id))
    clientposts = clientposts_result.scalars().all()
    driver_result = await session.execute(select(Driver).where(Driver.id == trip.driver_id))    
    driver = driver_result.scalars().first()
    await session.close()
    if clientposts:
        for clientpost in clientposts:
            clientpost_id = clientpost.id
            client_id = clientpost.client_user_id 
            another_taxi_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Дигар такси", callback_data=f"another_taxi:{clientpost_id}")],
                ])

            # Фиристодани паём ба мизоҷ
            await bot.send_message(
                chat_id=client_id,
                text=f"Ронанда: {driver.name}\n\n Аз {trip.from_city}\n ба {trip.to_city}\n шуморо қабул накард.\n\n Лутфан дигар таксиро заказ кунед.",
                reply_markup=another_taxi_keyboard
                )

        async with session.begin():    
            await session.execute(delete(ClientPost).where(ClientPost.selected_post_id == trip.id))
            await session.commit()
            await session.close()

    async with session.begin():
        await session.execute(update(DriverPost).where(DriverPost.id == trip_id).values(current_clients = int(0), is_online = False))
        await session.commit()
        await session.close()      
    # Гирифтани маълумоти навшудаи сафар
    trip_result = await session.execute(select(DriverPost).where(DriverPost.id == trip_id))
    trip = trip_result.scalars().first()

    await session.close()

    driver_info = (
            f"Маълумот дар бораи сафар:\n\n"
        f"Аз шаҳри: {trip.from_city}\n"
        f"Ба шаҳри: {trip.to_city}\n\n"
        f"Нарх: {trip.price}\n\n"
        f"Шумораи клиенти кабулкардашуда: {trip.current_clients}\n\n"
        f"Шумораи клиенти лозима: {trip.max_clients}\n\n"
        f"Комментария:\n {trip.comment if trip.comment else 'ронанда коментария нагузоштааст'}\n\n"
        f"Пости ОФЛАЙН-ро клиент дида наметавонад.\n\n"
        f"Ин пост: {'ОНЛАЙН аст.' if trip.is_online else 'ОФЛАЙН аст'}"
        )

        # Тугмаҳо барои оғози ва анҷоми ҷустуҷӯ, сафарҳои нав ва ҳазфи сафар
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Онлайн", callback_data=f"set_online:{trip.id}")],
        [InlineKeyboardButton(text="Офлайн", callback_data=f"set_offline:{trip.id}")],
        [InlineKeyboardButton(text="Удалить кардан", callback_data=f"delete_trip:{trip.id}")],
        [InlineKeyboardButton(text="Ба роҳ баромадан", callback_data=f"start_trip:{trip.id}")]
        ])

    await call.message.answer(driver_info, reply_markup=keyboard)    


   
    
        
        
        
        
# Удалит кардани сафар
@driver_router.callback_query(lambda call: call.data.startswith("delete_trip"))
async def delete_trip(call: CallbackQuery,):
    from bot import bot
    session = AsyncSessionLocal()
    trip_id = int(call.data.split(":")[1])
    trip_result = await session.execute(select(DriverPost).where(DriverPost.id == trip_id))
    trip = trip_result.scalars().first()
    clientposts_result = await session.execute(select(ClientPost).where(ClientPost.selected_post_id == trip.id))
    clientposts = clientposts_result.scalars().all()
    await session.close()
    if clientposts:
        for clientpost in clientposts:
            clientpost_id = clientpost.id
            client_id=clientpost.client_user_id 
            another_taxi_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Дигар такси", callback_data=f"another_taxi:{clientpost_id}")],
                ])

            # Фиристодани паём ба мизоҷ
            await bot.send_message(
                chat_id=client_id,
                text=f"Ронанда: {driver.name}\n\n Аз {trip.from_city}\n ба {trip.to_city}\n шуморо қабул накард.\n\n Лутфан дигар таксиро заказ кунед.",
                reply_markup=another_taxi_keyboard
                )

        async with session.begin():    
            await session.execute(delete(ClientPost).where(ClientPost.selected_post_id == trip.id))
            await session.commit()
            await session.close()
    async with session.begin():
        await session.execute(delete(DriverPost).where(DriverPost.id == trip_id))
        await session.commit()
        await session.close()
    
    await call.message.answer("Сафари шумо бомуваффақият удалит карда шуд.")

    driver_result = await session.execute(select(Driver).where(Driver.user_id == call.message.from_user.id))
    driver = driver_result.scalars().first()
    await session.close()
    driver_id = driver.id
    

    driver_trips_result = await session.execute(select(DriverPost).where(DriverPost.driver_id == driver_id).order_by(DriverPost.is_online, DriverPost.current_clients))
    driver_trips = driver_trips_result.scalars().all()
    await session.close()
    if driver_trips:
        

        for driver_trip in driver_trips:
            driver_info = (
                f"Маълумот дар бораи сафар:\n\n"
            f"Аз шаҳри: {driver_trip.from_city}\n"
            f"Ба шаҳри: {driver_trip.to_city}\n\n"
            f"Нарх: {driver_trip.price}\n\n"
            f"Шумораи клиенти кабулкардашуда: {driver_trip.current_clients}\n\n"
            f"Шумораи клиенти лозима: {driver_trip.max_clients}\n\n"
            f"Комментария:\n {driver_trip.comment if driver_trip.comment else 'ронанда коментария нагузоштааст'}\n\n"
            f"Пости ОФЛАЙН-ро клиент дида наметавонад.\n\n"
            f"Ин пост: {'ОНЛАЙН аст.' if driver_trip.is_online else 'ОФЛАЙН аст'}"
                )

            # Тугмаҳо барои оғози ва анҷоми ҷустуҷӯ, сафарҳои нав ва ҳазфи сафар
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Онлайн", callback_data=f"set_online:{driver_trip.id}")],
                [InlineKeyboardButton(text="Офлайн", callback_data=f"set_offline:{driver_trip.id}")],
                [InlineKeyboardButton(text="Удалить кардан", callback_data=f"delete_trip:{driver_trip.id}")],
                [InlineKeyboardButton(text="Ба роҳ баромадан", callback_data=f"start_trip:{driver_trip.id}")]
            ])


            await call.message.answer(driver_info, reply_markup=keyboard)
            await session.close()
    else:
        await call.message.answer("Шумо ҳанӯз маълумотҳои худро ворид накардаед.")

    await session.close()
    new_trip_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Сафари нав ба қайд гирифтан", callback_data="new_trip")],
    ])        
    await call.message.answer("Пост барои сафари нав нависед", reply_markup=new_trip_keyboard)

    
        
        
        
        
        
@driver_router.callback_query(lambda call: call.data == "new_trip")
async def start_new_trip(call: CallbackQuery, state: FSMContext):
    await start_trip_registration(call, state)
    
    
    
# Хандлер барои /account (фақат барои ронандагон)
@driver_router.message(Command("account"))
async def account_info(message: types.Message, state: FSMContext):
    session = AsyncSessionLocal()
    driver_result = await session.execute(select(Driver).where(Driver.user_id == message.from_user.id))
    driver = driver_result.scalars().first()
    await session.close()
    if driver:
        confirmation_text = (
            f"Аккаунти шумо:\n\n"
            f"Ном: {driver.name}\n"
            f"Рақами телефон: {driver.phone_number}\n"
            f"Баҳои Ронанда аз 1 то 5: {driver.avr_rating}\n"
            )


        car_images_from_db_result = await session.execute(select(CarImage).where(CarImage.driver_user_id == driver.user_id))
        car_images_from_db = car_images_from_db_result.scalars().all()
        await session.close()
        if car_images_from_db:
            media=[]    
            for car_image in car_images_from_db:
                car_img=car_image.file_id
                media.append(InputMediaPhoto(media=car_img))
            await message.answer_media_group(media)
            media.clear()
            
            # Тугма барои тасдиқ ё ивази маълумотҳо
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Ивази аккаунт", callback_data="edit_driver_account")]
            ])
            

            await message.answer(text=confirmation_text, reply_markup=markup)

        else:
            await session.delete(driver)
            await session.commit()
            await session.close()                            
            await message.answer('Шумо холо аккаунт надоред.\n Барои кушодани аккаунт лутфан номатонро нависед.' )
            await state.set_state(RegisterDriverFSM.waiting_for_name)
            
                            

    else:
        await message.answer('Шумо холо аккаунт надоред.\n Барои кушодани аккаунт лутфан номатонро нависед.' )
        await state.set_state(RegisterDriverFSM.waiting_for_name)

    
# Хандлер барои /my_posts (фақат барои ронандагон)
@driver_router.message(Command("my_posts"))
async def my_posts(message: types.Message, state: FSMContext):
    session = AsyncSessionLocal()

    driver_result = await session.execute(select(Driver).where(Driver.user_id == message.from_user.id))
    driver = driver_result.scalars().first()
    await session.close()
    if driver:
        driver_trips_result = await session.execute(select(DriverPost).where(DriverPost.driver_id == driver.id).order_by(DriverPost.is_online))
        driver_trips = driver_trips_result.scalars().all()
        await session.close()
        if driver_trips:
            
            for driver_trip in driver_trips:
                driver_info = (
                    f"Маълумот дар бораи сафар:\n\n"
                f"Аз шаҳри: {driver_trip.from_city}\n\n"
                f"Ба шаҳри: {driver_trip.to_city}\n\n"
                f"Нарх: {driver_trip.price}\n\n"
                f"Шумораи клиенти кабулкардашуда: {driver_trip.current_clients}\n\n"
                f"Шумораи клиенти лозима: {driver_trip.max_clients}\n\n"
                f"Комментария:\n {driver_trip.comment if driver_trip.comment else 'ронанда коментария нагузоштааст'}\n\n"
                f"Пости ОФЛАЙН-ро клиент дида наметавонад.\n\n"
                f"Ин пост: {'ОНЛАЙН аст.' if driver_trip.is_online else 'ОФЛАЙН аст'}"
                )

                # Тугмаҳо барои оғози ва анҷоми ҷустуҷӯ, сафарҳои нав ва ҳазфи сафар
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Онлайн", callback_data=f"set_online:{driver_trip.id}")],
                [InlineKeyboardButton(text="Офлайн", callback_data=f"set_offline:{driver_trip.id}")],
                [InlineKeyboardButton(text="Удалить кардан", callback_data=f"delete_trip:{driver_trip.id}")],
                [InlineKeyboardButton(text="Ба роҳ баромадан", callback_data=f"start_trip:{driver_trip.id}")]
                ])

                await message.answer(driver_info, reply_markup=keyboard)
            
        else:
            await message.answer("Шумо ҳанӯз маълумотҳои худро ворид накардаед.")


        new_trip_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сафари нав ба қайд гирифтан", callback_data="new_trip")],
        ])        
        await message.answer("Пост барои сафари нав нависед", reply_markup=new_trip_keyboard)

    else:
        await message.answer('Шумо холо аккаунт надоред.\n Барои кушодани аккаунт лутфан номатонро нависед.' )
        await state.set_state(RegisterDriverFSM.waiting_for_name)


    
# Хандлер барои /new_trip (фақат барои ронандагон)
@driver_router.message(Command("new_trip"))
async def new_trip(message: types.Message):
    new_trip_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Сафари нав ба қайд гирифтан", callback_data="new_trip")],
    ])        
    await message.answer("Пост барои сафари нав нависед", reply_markup=new_trip_keyboard)

# Хандлер барои /help (дастрас барои ҳама)
@driver_router.message(Command("taxi_channel"))
async def show_help(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Обуна шудан ба група", url="https://t.me/ronanda_bot")]
    ])
    await message.answer("Аз навигариҳо бохабар шавед.", reply_markup=keyboard)



# Хандлер барои қабул кардан
@driver_router.callback_query(lambda c: c.data.startswith("accept_"))
async def handle_accept_callback(call: types.CallbackQuery, state: FSMContext):
    from bot import bot
    session = AsyncSessionLocal()

    data = call.data.split("_")
    client_id = int(data[1])
    post_id = int(data[2])
    
    # Гирифтани мизоҷ ва пост аз базаи маълумот
    client_result = await session.execute(select(Client).where(Client.id == client_id))
    client = client_result.scalars().first()
    clientpost_result = await session.execute(select(ClientPost).where(ClientPost.client_user_id == client.user_id).order_by(desc(ClientPost.id)))
    clientpost = clientpost_result.scalars().first()
    post_result = await session.execute(select(DriverPost).where(DriverPost.id == post_id))
    post = post_result.scalars().first()
    await session.close()
    async with session.begin():
        await session.execute(update(ClientPost).where(ClientPost.id == clientpost.id).values(selected_post_id = post_id))
        await session.commit()
        await session.close()

    

    # Фиристодани паём ба ронанда
    await bot.send_message(
        chat_id=call.from_user.id,
        text=f"Шумо {client.name}-ро қабул кардед."
    )

    # Фиристодани паём ба мизоҷ
    await bot.send_message(
        chat_id=client.user_id,
        text=f"Ронанда {post.from_city} ба {post.to_city} шуморо қабул кард.\n\n Сафари хуб."
    )

 
    edited_post_result = await session.execute(select(DriverPost).where(DriverPost.id == post.id))
    edited_post = edited_post_result.scalars().first()
    await session.close()
    driver_info = (
            f"Маълумот дар бораи сафар:\n\n"
        f"Аз шаҳри: {edited_post.from_city}\n"
        f"Ба шаҳри: {edited_post.to_city}\n\n"
        f"Нарх: {edited_post.price}\n\n"
        f"Шумораи клиенти кабулкардашуда: {edited_post.current_clients}\n\n"
        f"Шумораи клиенти лозима: {edited_post.max_clients}\n\n"
        f"Комментария:\n {edited_post.comment if edited_post.comment else 'ронанда коментария нагузоштааст'}\n\n"
        f"Пости ОФЛАЙН-ро клиент дида наметавонад.\n\n"
        f"Ин пост: {'ОНЛАЙН аст.' if edited_post.is_online else 'ОФЛАЙН аст'}"
        )

    # Тугмаҳо барои оғози ва анҷоми ҷустуҷӯ, сафарҳои нав ва ҳазфи сафар
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Онлайн", callback_data=f"set_online:{edited_post.id}")],
        [InlineKeyboardButton(text="Офлайн", callback_data=f"set_offline:{edited_post.id}")],
        [InlineKeyboardButton(text="Удалить кардан", callback_data=f"delete_trip:{edited_post.id}")],
        [InlineKeyboardButton(text="Ба роҳ баромадан", callback_data=f"start_trip:{edited_post.id}")]
        ])

    await call.message.answer(driver_info, reply_markup=keyboard)
    await state.finish()
    
# Хандлер барои рад кардан
@driver_router.callback_query(lambda c: c.data.startswith("decline_"))
async def handle_decline_callback(call: types.CallbackQuery, state: FSMContext):

    from bot import bot
    session = AsyncSessionLocal()


    data = call.data.split("_")
    client_id = int(data[1])
    post_id = int(data[2])
    
    # Гирифтани мизоҷ ва пост аз базаи маълумот
    client_result = await session.execute(select(Client).where(Client.id == client_id))
    client = client_result.scalars().first()
    post_result = await session.execute(select(DriverPost).where(DriverPost.id == post_id))
    post = post_result.scalars().first()
    driver_result = await session.execute(select(Driver).where(Driver.id == post.driver_id))
    driver = driver_result.scalars().first()
    clientpost_result = await session.execute(select(ClientPost).where(ClientPost.client_user_id == client.user_id).order_by(desc(ClientPost.id)))
    clientpost = clientpost_result.scalars().first()
    clientpost_id = clientpost.id
    await session.close()
    if clientpost and clientpost.selected_post_id == post_id:
        try:
            async with session.begin():
                new_current_clients = int(post.current_clients) - int(clientpost.num_clients)
                await session.execute(update(DriverPost).where(DriverPost.id == post.id).values(current_clients = new_current_clients))
                await session.commit()
                await session.close()
        except Exception as e:
            await call.message.answer(f"Хатогӣ: {str(e)}")
            return

        await session.delete(clientpost)
        await session.commit()
        await session.close()
        # Фиристодани паём ба ронанда
        await bot.send_message(
            chat_id=call.from_user.id,
            text=f"Шумо {client.name}-ро қабул накардед."
        )


        another_taxi_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Дигар такси", callback_data=f"another_taxi:{clientpost_id}")],
        ])

        # Фиристодани паём ба мизоҷ
        await bot.send_message(
            chat_id=client.user_id,
            text=f"Ронанда: {driver.name}\n\n Аз {post.from_city}\n ба {post.to_city}\n шуморо қабул накард.\n\n Лутфан дигар таксиро заказ кунед.",
            reply_markup=another_taxi_keyboard
        )
        
        await state.finish()

 

@driver_router.callback_query(lambda call: call.data.startswith("start_trip"))
async def start_trip(call: CallbackQuery):
    from bot import bot
    session = AsyncSessionLocal()
    trip_id = int(call.data.split(":")[1])
    trip_result = await session.execute(select(DriverPost).where(DriverPost.id == trip_id))
    trip = trip_result.scalars().first()
    driver_result = await session.execute(select(Driver).where(Driver.id == trip.driver_id))
    driver = driver_result.scalars().first()
    clienttrips_result = await session.execute(select(ClientPost).where(ClientPost.selected_post_id == trip.id))
    clienttrips = clienttrips_result.scalars().all()
    await session.close()
    async with session.begin():
        await session.execute(update(DriverPost).where(DriverPost.id == trip_id).values(is_online = False, current_clients = 0))
        await session.commit()
        await session.close()
    if clienttrips:
        for clienttrip in clienttrips:
            client_result = await session.execute(select(Client).where(Client.user_id == clienttrip.client_user_id))
            client = client_result.scalars().first()
            await bot.send_message(
                chat_id=client.user_id,
                text=f"Ронанда: {driver.name}\n\n Аз {trip.from_city}\n ба {trip.to_city} ба сафар баромад.\n\n РОҲИ САФЕД"
                )
    end_trip_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=f"Ба шаҳри {trip.to_city} расидем", callback_data=f"end_trip:{trip.id}")]
                        ])

    await call.message.answer("РОҲИ САФЕД", reply_markup=end_trip_keyboard)
    await session.close()

@driver_router.callback_query(lambda call: call.data.startswith("end_trip"))
async def end_trip(call: CallbackQuery):
    from bot import bot
    
    trip_id = int(call.data.split(":")[1])

    session = AsyncSessionLocal()
    trip_result = await session.execute(select(DriverPost).where(DriverPost.id == trip_id))
    trip = trip_result.scalars().first()
    driver_result = await session.execute(select(Driver).where(Driver.id == trip.driver_id))
    driver = driver_result.scalars().first()
    clientpost_result = await session.execute(select(ClientPost).where(ClientPost.selected_post_id == trip.id))
    clientpost = clientpost_result.scalars().all()
    await session.close()
    # Ба ҳамаи клиентҳое, ки дар сафар буданд, паём фиристода шавад
    for client in clientpost:
        client_id=client.client_user_id
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1", callback_data=f"rate:{trip.driver_id}:1:{trip.id}"), InlineKeyboardButton(text="2", callback_data=f"rate:{trip.driver_id}:2:{trip.id}")],
            [InlineKeyboardButton(text="3", callback_data=f"rate:{trip.driver_id}:3:{trip.id}"), InlineKeyboardButton(text="4", callback_data=f"rate:{trip.driver_id}:4:{trip.id}")],
            [InlineKeyboardButton(text="5", callback_data=f"rate:{trip.driver_id}:5:{trip.id}")]
        ])
            
        await bot.send_message(client_id, f"Лутфан ба ронандаи {driver.name} баҳо гузоред:", reply_markup=keyboard)

    # Ҳамаи объектҳои `clientpost`-ро якбора нест кунед
    await session.execute(delete(ClientPost).where(ClientPost.selected_post_id == trip.id))
    await session.commit()
    await session.close()
    
    await call.message.answer(f"Сафари бо ID {trip_id} ба итмом расид.")
    

@driver_router.message(Command("my_clients"))
async def my_posts(message: types.Message):
    session = AsyncSessionLocal()
    user_id = message.from_user.id
    
    driver_result = await session.execute(select(Driver).where(Driver.user_id == user_id))
    driver = driver_result.scalars().first()
    driverposts_result = await session.execute(select(DriverPost).where(DriverPost.driver_id == driver.id))
    driverposts = driverposts_result.scalars().all()
    await session.close()
    for driverpost in driverposts:
        
        clientposts_result = await session.execute(select(ClientPost).where(ClientPost.selected_post_id == driverpost.id))
        clientposts = clientposts_result.scalars().all()
        await session.close()
        if clientposts:
            for clientpost in clientposts:
                client_result = await session.execute(select(Client).where(Client.user_id == clientpost.client_user_id))
                client = client_result.scalars().first()
                client_info = (
                        f"Маълумот дар бораи клиент:\n\n"
                    f"Аз шаҳри: {clientpost.from_city}\n\n"
                    f"Ба шаҳри: {clientpost.to_city}\n\n"
                    f"Номи клиент: {client.name}\n\n"
                    f"Рақами телефон: {client.phone_number}\n\n"
                    f"Нарх: {driverpost.price}\n\n"
                    f"Шумораи клиент: {clientpost.num_clients}\n\n"
                    )

                # Эҷоди тугмаҳои қабул ва рад
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Рад кардан", callback_data=f"decline_{client.id}_{driverpost.id}")]
                    ])
                    
                    
                await message.answer(client_info, reply_markup=keyboard)
                await session.close()            
        else:
            await message.answer(f"Шумо ҳанӯз барои\n\n Пост бо id: {driverpost.id}\n\n Аз {driverpost.from_city}\n Ба {driverpost.to_city}\n\n клиент надоред.")
                
