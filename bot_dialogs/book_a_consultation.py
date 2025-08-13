import re
import os
from dotenv import load_dotenv
from typing import Any

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Calendar, Column, Select, CalendarConfig, Back, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from datetime import date, timezone, timedelta

import data_file
import states
from bot_database.database import Database

load_dotenv()

async def on_date_selected(callback: CallbackQuery, widget,
                           manager: DialogManager, selected_date: date):
    if selected_date.weekday() in (5, 6):
        await callback.answer("❌ У вихідні дні запис неможливий", show_alert=True)
        return

    manager.dialog_data["selected_date"] = selected_date.isoformat()
    await callback.answer(f"Дата обрана: {selected_date}")
    await manager.next()


async def get_data(dialog_manager: DialogManager, **kwargs):
    request: Database = dialog_manager.middleware_data["request"]
    date_str = dialog_manager.dialog_data.get("selected_date")
    booked_time = await request.get_time(date_str)
    slots = [x for x in data_file.time_slots if x[0] not in booked_time]

    return {
        "slots": slots,
    }

async def on_time_selected(callback: CallbackQuery, widget: Any,
                            manager: DialogManager, item_id: str):
    print("slots selected: ", item_id)
    manager.dialog_data["selected_time"] = item_id
    await callback.answer(f"Час обрано: {item_id}")
    await manager.next()


async def on_phone_entered(message: Message,
                           widget: TextInput,
                           manager: DialogManager,
                           text: str):
    phone = text.strip()
    pattern = re.compile(r"^(\+?380\d{9}|0\d{9})$")
    if not pattern.fullmatch(phone):
        await message.answer("❗ Невірний формат номера.\nПриклади:\n +380991234567\n 0991234567")
        return
    manager.dialog_data["phone"] = phone
    await manager.next()


async def on_problem_entered(message: Message, widget: TextInput,
                             manager: DialogManager, text: str):
    request: Database = manager.middleware_data["request"]

    manager.dialog_data["problem_description"] = text

    date_str = manager.dialog_data.get("selected_date")
    time_str = manager.dialog_data.get("selected_time")
    phone_str = manager.dialog_data.get("phone")
    user = message.from_user

    await request.add_info(user_id=user.id,
                           user_name=user.username,
                           phone_number=phone_str,
                           date=date_str,
                           time=time_str,
                           problem_descr=text)
    await message.answer(
        f"✅ Дякуємо за довіру!\n"
        f"Ви записані на консультацію {date_str} о {time_str}.\n"
        f"📄 Чекаємо вас за адресою м. Київ"
    )
    try:
        await manager.middleware_data["bot"].send_message(
            chat_id=os.getenv('LAWYER_ID'),
            text=f"Запис на консультацію @{user.username or user.first_name}\n"
                 f"{date_str} о {time_str}\n"
                 f"tel: {phone_str}\n"
                 f"{text}"
        )
    except Exception as e:
        print(f"❌ Ошибка при отправке администратору: {e}")

    await manager.done()


async def go_back(callback: CallbackQuery, button: Button,
                  manager: DialogManager):
    await callback.answer('Запис скасовано')
    await manager.done()


appointment_for_a_consultation_dialog = Dialog(
    Window(
        Const("📅 Оберіть дату консультації:"),
        Calendar(id='calendar',
                 on_click=on_date_selected,
                 config=CalendarConfig(firstweekday=0,
                                       timezone=timezone(timedelta(hours=2)),
                                       min_date=date.today(),
            )),
        Button(Const("⬅️"), id="back", on_click=go_back),
        state=states.Consultation.choose_date
    ),
    Window(
        Format("🗓 Ви обрали дату: {dialog_data[selected_date]}\n\n"
               "⏰ Оберіть зручний час:"),
        Column(Select(
            Format("{item[0]}"),
            id="s_slots",
            item_id_getter=lambda item: str(item[0]),
            items="slots",
            on_click=on_time_selected,
        )
        ),
        Back(Const("Назад")),
        getter=get_data,
        state=states.Consultation.choose_time
    ),
    Window(
        Format("🗓 Ви обрали дату: {dialog_data[selected_date]}\n"
               "⏰ та час: {dialog_data[selected_time]}\n\n"
               "📞 Введіть свій номер телефону:"),
        TextInput(id="phone_input", on_success=on_phone_entered),
        Back(Const("Назад")),
        state=states.Consultation.enter_phone
    ),
    # Шаг 3: Ввод описания
    Window(
        Format("📝 Опишіть коротко суть питання:"),
        TextInput(id="problem_input", on_success=on_problem_entered),
        state=states.Consultation.enter_problem
    )
)
