"""Bot states for FSM (Finite State Machine)."""
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Registration flow states."""
    waiting_for_full_name = State()
    waiting_for_phone = State()


class ApartmentStates(StatesGroup):
    """Apartment creation flow states."""
    waiting_for_type = State()
    waiting_for_rooms = State()
    waiting_for_address = State()
    waiting_for_address_detail = State()
    waiting_for_location = State()
    waiting_for_price = State()
    waiting_for_area = State()
    waiting_for_floor = State()
    waiting_for_total_floors = State()
    waiting_for_description = State()
    waiting_for_photos = State()
    confirm_apartment = State()
    choosing_edit_field = State()


class AdminStates(StatesGroup):
    """Admin flow states."""
    waiting_for_broadcast_message = State()
    waiting_for_user_search = State()


class ImportStates(StatesGroup):
    """Admin 'forward import' flow: a forwarded/pasted post -> parsed listing."""
    waiting_for_post = State()
    waiting_for_phone = State()
