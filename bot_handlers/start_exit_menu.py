from aiogram import Router
from aiogram_dialog import DialogManager, StartMode
from aiogram.filters import CommandStart
from aiogram.types import Message

import states


router: Router = Router()
@router.message(CommandStart())
async def user_start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.MainMenu.main, mode=StartMode.RESET_STACK)