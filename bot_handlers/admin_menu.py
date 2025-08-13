from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

import data_file
from bot_filters import AdminFilter
from bot_keyboards import callback_keyboards as keyboard


router: Router = Router()


@router.message(CommandStart(), AdminFilter())
async def admin_start(message: Message):
    await message.answer(
        "hello admin",
        reply_markup=keyboard.keyboard_builder(width=1, **data_file.ADMIN_BUTTONS)
    )


@router.callback_query(F.data == "main_menu")
async def process_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "hello admin",
        reply_markup=keyboard.keyboard_builder(width=1, **data_file.ADMIN_BUTTONS)
    )