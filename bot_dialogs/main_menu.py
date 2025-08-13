from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Multi
from aiogram_dialog.widgets.kbd import Row

import states
from bot_handlers.main_menu_handlers import go_to_selection


main_menu_dialog = Dialog(
    Window(
        Multi(
            Const('Вітаємо в Цифровому кабінеті\nАдвокатського бюро Сергія Філатова.'),
            Const("Оберіть опцію, яка вас цікавить:"),
            sep="\n\n",
        ),
        Button(
            Const('Записатися на консультацію 📅'),
            id='appointment',
            on_click=go_to_selection
        ),
        Button(
            Const('Залишити запитання адвокату ⚖️'),
            id='question_for_lawyer',
            on_click=go_to_selection
        ),
        Button(
            Const('Мої справи'),
            id='my_cases',
            on_click=go_to_selection
        ),
        Row(
            Button(Const('Часті запитання'), id='faq', on_click=go_to_selection),
            Button(Const('Про бюро️'), id="about", on_click=go_to_selection),
        ),
        state=states.MainMenu.main,
    )
)




