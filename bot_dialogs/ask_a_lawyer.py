from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.input import MessageInput

import states
from bot_handlers.customer_question import handle_question


ask_lawyer_dialog = Dialog(
    Window(
        Const("📝 Опишіть суть вашої проблеми, і адвокат відповість найближчим часом."),
        MessageInput(handle_question),
        state=states.AskLawyer.ask
    ),
    Window(
        Const("✅ Дякуємо, ваше повідомлення надіслано адвокату. Очікуйте відповідь."),
        Button(Const("⬅️ Назад до меню"), id="back_to_main", on_click=lambda c, b, m: m.start(states.MainMenu.main)),
        state=states.AskLawyer.thanks
    )
)
