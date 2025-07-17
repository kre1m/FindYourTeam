from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
class RegisterStates(StatesGroup):
    name = State()
    city = State()
    skills = State()
    looking_for = State()
    experience = State()
    photo_id = State()
    description = State()

class PhotoUpdateState(StatesGroup):
    waiting_for_photo = State()

class SearchStates(StatesGroup):
    active_search = State()

class FilterStates(StatesGroup):
    choosing_filters = State()
    filter_city = State()
    filter_experience = State()
    filter_photo = State()
    confirming_filters = State()
    searching = State()
