from aiogram import Router
from aiogram_dialog import DialogManager, StartMode
from aiogram.filters import CommandStart
from aiogram.types import Message

import data_file
import states
from bot_keyboards import callback_keyboards as keyboard
from config import settings

router: Router = Router()


# @router.message(CommandStart())
# async def process_start_command(message: Message, dialog_manager: DialogManager):
#     user = message.from_user
#     if user.id != settings.admin_id:
#         await dialog_manager.start(states.MainMenu.main, mode=StartMode.RESET_STACK)
#     elif user.id == settings.admin_id:
#         await message.answer(text='hello admin',
#                              reply_markup=keyboard.keyboard_builder(width=1, **data_file.ADMIN_BUTTONS))

@router.message(CommandStart())
async def user_start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.MainMenu.main, mode=StartMode.RESET_STACK)