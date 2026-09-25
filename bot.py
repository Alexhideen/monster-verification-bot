import os
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

pending = {}


@dp.chat_join_request()
async def new_request(request: ChatJoinRequest):
    user = request.from_user

    pending[user.id] = {
        "chat_id": request.chat.id,
        "user_id": user.id,
        "name": user.full_name,
    }

    await bot.send_message(
        user.id,
        "привет 👋\n\n"
        "для вступления в группу напиши сегодняшнюю дату "
        "в формате дд.мм.гггг"
    )


@dp.message(F.text == "/id")
async def get_id(message: Message):
    await message.answer(f"🆔 id этого чата: `{message.chat.id}`")


@dp.message(F.chat.type == "private")
async def answer(message: Message):
    user_id = message.from_user.id

    if user_id not in pending:
        return

    today = datetime.now().strftime("%d.%m.%Y")
    answer_text = message.text.strip()

    data = pending[user_id]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ принять",
                    callback_data=f"approve:{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ отклонить",
                    callback_data=f"reject:{user_id}"
                )
            ]
        ]
    )

    await bot.send_message(
        ADMIN_CHAT_ID,
        f"🔔 новая заявка\n\n"
        f"👤 {data['name']}\n"
        f"🆔 {user_id}\n"
        f"📅 ответ: {answer_text}\n"
        f"📌 правильная дата: {today}",
        reply_markup=keyboard
    )

    await message.answer("ответ получен. ожидайте решения администратора.")


@dp.callback_query(F.data.startswith("approve:"))
async def approve(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])

    if user_id not in pending:
        await callback.answer("заявка уже обработана")
        return

    data = pending[user_id]

    await bot.approve_chat_join_request(
        chat_id=data["chat_id"],
        user_id=user_id
    )

    await bot.send_message(
        user_id,
        "✅ заявка одобрена. добро пожаловать!"
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("пользователь принят")

    del pending[user_id]


@dp.callback_query(F.data.startswith("reject:"))
async def reject(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])

    if user_id not in pending:
        await callback.answer("заявка уже обработана")
        return

    data = pending[user_id]

    await bot.decline_chat_join_request(
        chat_id=data["chat_id"],
        user_id=user_id
    )

    await bot.send_message(
        user_id,
        "❌ заявка отклонена."
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("заявка отклонена")

    del pending[user_id]


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
