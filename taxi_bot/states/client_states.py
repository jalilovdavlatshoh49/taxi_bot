from aiogram.fsm.state import State, StatesGroup

# Класи FSM барои ҳолатҳо
class ClientPostFSM(StatesGroup):
    waiting_for_from_city = State()
    waiting_for_to_city = State()
    waiting_for_selected_post_id = State()
    waiting_for_num_clients = State()

# Класи FSM барои ҳолатҳо
class ClientRegistrationFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone_number = State()

class EditClientInfo(StatesGroup):
    waiting_for_new_value = State()
