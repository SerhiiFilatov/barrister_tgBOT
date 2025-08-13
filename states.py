from aiogram.fsm.state import StatesGroup, State

class MainMenu(StatesGroup):
    main = State()


class ServiceSelection(StatesGroup):
    selection = State()


class FAQ(StatesGroup):
    view = State()
    access = State()
    consultation = State()


class AskLawyer(StatesGroup):
    ask = State()
    thanks = State()


class Consultation(StatesGroup):
    choose_date = State()
    choose_time = State()
    enter_phone = State()
    enter_problem = State()


class PhoneRequest(StatesGroup):
    enter_phone = State()