from aiogram.fsm.state import StatesGroup, State


class Gen(StatesGroup):
    initial_state = State()
    chat_state = State()

