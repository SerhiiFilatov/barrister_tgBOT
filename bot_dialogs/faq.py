from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

import states

faq_dialog = Dialog(
    Window(
        Const("❓ Часті запитання:\n\n1. Як записатися на консультацію?\n2. Як отримати доступ до справи?"),
        Button(Const("⬅️ Назад"), id="back", on_click=lambda c, b, m: m.start(states.MainMenu.main)),
        state=states.FAQ.view
    )
)
