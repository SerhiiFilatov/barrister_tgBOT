import os
from dotenv import load_dotenv

from aiogram import Router
from aiogram_dialog import DialogManager
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_dialog.widgets.common import ManagedWidget

import states
# from config import settings
from bot_database.database import Database

router: Router = Router()
load_dotenv()

async def handle_question(message: Message, widget: ManagedWidget, manager: DialogManager):
    request: Database = manager.middleware_data["request"]

    user = message.from_user
    text = message.text

    # admin_kb = InlineKeyboardMarkup(inline_keyboard=[
    #     [
    #         InlineKeyboardButton(text="✅ Прийняти", callback_data=f"accept_question:{user.id}"),
    #         InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_question:{user.id}")
    #     ]
    # ])
    await request.add_question(user_id=user.id,
                               user_name=user.username,
                               problem_descr=text)
    try:
        await manager.middleware_data["bot"].send_message(
            chat_id=os.getenv('LAWYER_ID'),
            text=f"📩 Нове питання від користувача @{user.username or user.first_name}:\n\n{text}",
            # reply_markup=admin_kb
        )
        await manager.switch_to(states.AskLawyer.thanks)
    except Exception as e:
        print(f"❌ Ошибка при отправке администратору: {e}")
