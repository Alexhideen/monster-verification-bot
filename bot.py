import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    ChatJoinRequest,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

TOKEN = "8902602483:AAHFH874cYN0LqwIYPtzDwKw-EaIlyu2bLg"

ADMIN_ID = 8547664737

bot = Bot(TOKEN)
dp = Dispatcher()

pending = {}


@dp.chat_join_request()
async def join_request_handler(event: ChatJoinRequest):
    pending[event.from_user.id] = {
        "chat_id": event.chat.id,
        "user_id": event.from_user.id,
    }

    try:
        await bot.send_message(
            event.user_chat_id,
            "привет 👋\n\n"
            "для вступления в чат «отель монстров» "
            "отправь кружок, в котором назовёшь сегодняшнюю дату."
        )
    except:
        pass


@dp.message(F.video_note)
async def video_note_handler(message: Message):

    user_id = message.from_user.id

    if user_id not in pending:
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ принять",
                    callback_data=f"approve:{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ отклонить",
                    callback_data=f"decline:{user_id}"
                ),
            ]
        ]
    )

    await bot.send_video_note(
        ADMIN_ID,
        message.video_note.file_id
    )

    await bot.send_message(
        ADMIN_ID,
        f"заявка от {message.from_user.full_name}",
        reply_markup=kb
    )


@dp.callback_query(F.data.startswith("approve:"))
async def approve(callback: CallbackQuery):

    user_id = int(callback.data.split(":")[1])
    data = pending.get(user_id)

    if not data:
        return

    await bot.approve_chat_join_request(
        chat_id=data["chat_id"],
        user_id=user_id
    )

    await callback.message.edit_text(
        "✅ пользователь принят"
    )

    pending.pop(user_id, None)


@dp.callback_query(F.data.startswith("decline:"))
async def decline(callback: CallbackQuery):

    user_id = int(callback.data.split(":")[1])
    data = pending.get(user_id)

    if not data:
        return

    await bot.decline_chat_join_request(
        chat_id=data["chat_id"],
        user_id=user_id
    )

    await callback.message.edit_text(
        "❌ пользователь отклонён"
    )

    pending.pop(user_id, None)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
