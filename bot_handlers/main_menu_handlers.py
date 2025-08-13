from aiogram_dialog import DialogManager

import states


async def go_to_selection(callback, button, manager: DialogManager):
    match button.widget_id:
        case "faq":
            await manager.start(states.FAQ.view)
        case "appointment":
            await manager.start(states.Consultation.choose_date)
        case "question_for_lawyer":
            await manager.start(states.AskLawyer.ask)
        case "my_cases":
            await manager.start(states.ServiceSelection.selection)
        case "about":
            await manager.start(states.ServiceSelection.selection)