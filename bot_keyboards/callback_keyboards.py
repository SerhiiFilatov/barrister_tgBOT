from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class NumbersCallbackFactory(CallbackData, prefix="num"):
    action: str
    index: int

def admin_panel():
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    buttons.append(InlineKeyboardButton(text='admin', callback_data='admin'))
    kb_builder.row(*buttons, width=1)
    return kb_builder.as_markup()


def keyboard_builder(width: int,  **kwargs) -> InlineKeyboardMarkup:
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    for text, callback in kwargs.items():
        buttons.append(InlineKeyboardButton(text=text, callback_data=callback))
    kb_builder.row(*buttons, width=width)
    return kb_builder.as_markup()

kb_go_back = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def keyboard_builder_2(index: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="<<<", callback_data=NumbersCallbackFactory(action="prev", index=index))
    kb.button(text=">>>", callback_data=NumbersCallbackFactory(action="next", index=index))
    kb.button(text="Ответить", callback_data=NumbersCallbackFactory(action="answer", index=index))
    kb.button(text="🏠 Главное меню", callback_data="main_menu")

    kb.adjust(2, 1, 1)
    return kb.as_markup()