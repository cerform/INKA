from aiogram.fsm.state import StatesGroup, State

class BookingStates(StatesGroup):
    selecting_service = State()
    selecting_master = State()
    selecting_date = State()
    selecting_time = State()
    entering_contact_info = State()
    confirming = State()
