
from aiogram.fsm.state import State, StatesGroup



# Ҳолатҳои FSM барои бақайдгирии ронанда
class RegisterDriverFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    
class CarImageFSM(StatesGroup):
    waiting_for_car_image=State()


class EditDriverInfo(StatesGroup):
    waiting_for_new_value = State()


class DriverTripFSM(StatesGroup):
    from_city = State()
    to_city = State()
    price = State()
    max_clients = State()
    comment = State()

