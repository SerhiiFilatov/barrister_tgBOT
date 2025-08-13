from aiogram.fsm.state import StatesGroup, State

class AnswerQuestion(StatesGroup):
    waiting_for_answer = State()