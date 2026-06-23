from aiogram.fsm.state import State, StatesGroup

class SupportStates(StatesGroup):
    waiting_for_problem = State()
    waiting_for_code = State()
    waiting_for_dev_message = State()
