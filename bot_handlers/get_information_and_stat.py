from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot_database.database import Database
from bot_keyboards.callback_keyboards import kb_go_back, keyboard_builder_2, NumbersCallbackFactory
from bot_database.fsm_factory import AnswerQuestion
router: Router = Router()


@router.callback_query(F.data == "consultations")
async def get_consult_info(callback: CallbackQuery, request: Database):
    get_info = await request.get_consult()
    text = "📋 Записи на консультацию:\n\n"
    for record in get_info:
        text += (
            f"👤 Пользователь: {record['user_name']} ({record['phone_number']})\n"
            f"📅 Дата: {record['date']}\n"
            f"🕒 Время: {record['time']}\n"
            f"💬 Описание: {record['problem_descr']}\n"
            f"---------------------------------\n"
        )
    await callback.message.edit_text(text=text, reply_markup=kb_go_back)


async def show_question(message_or_callback, questions, index: int):
    question = questions[index]
    text = (
        f"📋 Питання {index+1}/{len(questions)}\n\n"
        f"👤 {question['user_name']}\n"
        f"💬 {question['problem_descr']}"
    )

    kb = keyboard_builder_2(index)

    if hasattr(message_or_callback, "message"):  # CallbackQuery
        await message_or_callback.message.edit_text(text=text, reply_markup=kb)
    else:
        await message_or_callback.answer(text, reply_markup=kb)


@router.callback_query(F.data == "questions")
async def get_questions_info(callback: CallbackQuery, request: Database):
    questions = await request.get_questions()

    if not questions:
        await callback.message.edit_text("📭 Питань немає", reply_markup=kb_go_back)
        return

    await show_question(callback, questions, 0)


@router.callback_query(NumbersCallbackFactory.filter(F.action.in_(["next", "prev"])))
async def change_question(callback: CallbackQuery, callback_data: NumbersCallbackFactory, request: Database):
    questions = await request.get_questions()
    if not questions:
        await callback.message.edit_text("📭 Питань немає", reply_markup=kb_go_back)
        return

    index = callback_data.index
    if callback_data.action == "next":
        index = (index + 1) % len(questions)
    elif callback_data.action == "prev":
        index = (index - 1) % len(questions)

    await show_question(callback, questions, index)


@router.callback_query(NumbersCallbackFactory.filter(F.action == "answer"))
async def start_answer(callback: CallbackQuery, callback_data: NumbersCallbackFactory, request: Database, state: FSMContext):
    questions = await request.get_questions()
    question = questions[callback_data.index]

    await state.update_data(
        question_id=question["id"],
        question_index=callback_data.index
    )

    await callback.message.edit_text(
        f"📝 Ви обрали питання: \n\n"
        f"👤 {question['user_name']}\n"
        f"💬 {question['problem_descr']}\n\n"
        f"✍️ Введіть вашу відповідь: "
    )

    await state.set_state(AnswerQuestion.waiting_for_answer)


@router.message(AnswerQuestion.waiting_for_answer)
async def process_answer(message: Message, state: FSMContext, request: Database, bot: Bot):
    data = await state.get_data()
    question_id = data["question_id"]
    question_index = data["question_index"]

    question = await request.get_question_by_id(question_id)

    await bot.send_message(
        chat_id=question["user_id"],
        text=f"💌 Відповідь на ваше питання: \n\n{message.text}"
    )
    print(message.text)

    await message.answer("✅ Відповідь відправлена користувачу.")

    questions = await request.get_questions()

    if not questions:
        await message.answer("🎉 Усі питання оброблені!")
        await state.clear()
        return

    if question_index >= len(questions):
        question_index = 0

    await show_question(message, questions, question_index)
    await request.mark_question_as_executed(answer=message.text, question_id=question_id)
    await state.clear()
