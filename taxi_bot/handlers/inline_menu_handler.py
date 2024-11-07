from aiogram.filters import Command
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from db.database import Driver, Client, DriverPost, ClientPost, CarImage, AsyncSessionLocal
from keyboards.pagination import generate_pagination_keyboard
from states.driver_states import RegisterDriverFSM
from sqlalchemy import select
from states.client_states import ClientPostFSM, ClientRegistrationFSM
from start_handler import start_router



# Функсияи асосӣ барои /menu
@start_router.message(Command("menu"))
async def menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Обуна шудан ба група", url="https://t.me/ronanda_bot")],
        [InlineKeyboardButton(text="Фармоиши такси", callback_data="inline_order_taxi")],
        [InlineKeyboardButton(text="Клиентҳои ронанда", callback_data="inline_my_clients")],
        [InlineKeyboardButton(text="Ронандаи ман", callback_data="inline_my_driver")],
        [InlineKeyboardButton(text="Аккаунт барои клиент", callback_data="inline_client_account")],
        [InlineKeyboardButton(text="Постҳои ронанда", callback_data="inline_my_posts")],
        [InlineKeyboardButton(text="Аккаунт барои ронанда", callback_data="inline_driver_account")],
        [InlineKeyboardButton(text="Бақайдгирии сафари нав", callback_data="inline_new_trip")]
    ])

    await message.answer("Меню:", reply_markup=keyboard)

# Ҳангоми пахши тугмаҳои меню
@start_router.callback_query(lambda c: c.data)
async def process_callback(call: types.CallbackQuery, state: FSMContext):
    data = call.data
    user_id = call.from_user.id
    if data == "inline_order_taxi":
        keyboard = generate_pagination_keyboard(page=0, callback_prefix="client_from_city")
        await call.message.answer("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
        await state.set_state(ClientPostFSM.waiting_for_from_city)

    elif data == "inline_my_clients":
        session = AsyncSessionLocal()
        driver_result = await session.execute(select(Driver).where(Driver.user_id == user_id))
        driver = driver_result.scalars().first()
        driverposts_result = await session.execute(select(DriverPost).where(DriverPost.driver_id == driver.id))
        driverposts = driverposts_result.scalars().all()
        await session.close()
        if not driverposts:
            await call.message.answer(f"Шумо ҳанӯз клиент надоред.")
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
                        f"Нарх: {driverpost.price}\n\n"
                        f"Шумораи клиент: {clientpost.num_clients}\n\n"
                        )

                    # Эҷоди тугмаҳои қабул ва рад
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Рад кардан", callback_data=f"decline_{client.id}_{driverpost.id}")]
                        ])
                    
                    
                    await call.message.answer(client_info, reply_markup=keyboard)
                    await session.close()            
            else:
                await call.message.answer(f"Шумо ҳанӯз барои\n\n Пост бо id: {driverpost.id}\n\n Аз {driverpost.from_city}\n Ба {driverpost.to_city}\n\n клиент надоред.")
                
    elif data == "inline_client_account":
        session = AsyncSessionLocal()
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
            await call.message.answer(confirmation_text, reply_markup=markup)
        else:
            client_registration_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="регистратсия", callback_data="client_registration")],
                    ])

            await call.message.answer("Ҳануз барои заказ кардани таксӣ аккаунт надоред.\n\n Лутфан регистратсия кунед", reply_markup=client_registration_keyboard)

    elif data == "inline_my_posts":
        session = AsyncSessionLocal()
        driver_result = await session.execute(select(Driver).where(Driver.user_id == user_id))
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

                    await call.message.answer(driver_info, reply_markup=keyboard)
                
            else:
                await call.message.answer("Шумо ҳанӯз маълумотҳои худро ворид накардаед.")


            new_trip_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Сафари нав ба қайд гирифтан", callback_data="new_trip")],
            ])        
            await call.message.answer("Пост барои сафари нав нависед", reply_markup=new_trip_keyboard)

        else:
            await call.message.answer('Шумо холо аккаунт надоред.\n Барои кушодани аккаунт лутфан номатонро нависед.' )
            await state.set_state(RegisterDriverFSM.waiting_for_name)

    elif data == "inline_driver_account":
        session = AsyncSessionLocal()
        driver_result = await session.execute(select(Driver).where(Driver.user_id == user_id))
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
                await call.message.answer_media_group(media)
                media.clear()
                
                # Тугма барои тасдиқ ё ивази маълумотҳо
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Ивази аккаунт", callback_data="edit_driver_account")]
                ])
                

                await call.message.answer(text=confirmation_text, reply_markup=markup)

            else:
                await session.delete(driver)
                await session.commit()
                await session.close()                            
                await call.message.answer('Шумо холо аккаунт надоред.\n Барои кушодани аккаунт лутфан номатонро нависед.' )
                await state.set_state(RegisterDriverFSM.waiting_for_name)
                
                                

        else:
            await call.message.answer('Шумо холо аккаунт надоред.\n Барои кушодани аккаунт лутфан номатонро нависед.' )
            await state.set_state(RegisterDriverFSM.waiting_for_name)

    elif data == "inline_new_trip":
        new_trip_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Сафари нав ба қайд гирифтан", callback_data="new_trip")],
            ])        
        await call.message.answer("Пост барои сафари нав нависед", reply_markup=new_trip_keyboard)

    elif data == "inline_my_driver":
        session = AsyncSessionLocal()
        
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
                
                car_images_from_db_result = await session.execute(select(CarImage).where(CarImage.driver_user_id == driver.user_id))
                car_images_from_db = car_images_from_db_result.scalars().all()
                await session.close()
                media=[]    
                for car_image in car_images_from_db:
                    car_img=car_image.file_id
                    media.append(InputMediaPhoto(media=car_img))
                await call.message.answer_media_group(media)
                media.clear()
                



                await call.message.answer(text=driver_info, reply_markup=keyboard)
                    
        else:
            await call.message.answer("Шумо ҳанӯз такси заказ накардаед.")
            keyboard = generate_pagination_keyboard(page=0, callback_prefix="client_from_city")
            await call.message.answer("Аз кадом шаҳр сафарро оғоз мекунед?", reply_markup=keyboard)
            await state.set_state(ClientPostFSM.waiting_for_from_city)


