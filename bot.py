import asyncio
import os

from flask import Flask, request
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    ChatJoinRequest,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Update,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8547664737

bot = Bot(TOKEN)
dp = Dispatcher()
app = Flask(__name__)

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
    except Exception:
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
        await callback.answer("заявка уже обработана")
        return

    await bot.approve_chat_join_request(
        chat_id=data["chat_id"],
        user_id=user_id
    )

    await callback.message.edit_text("✅ пользователь принят")
    await callback.answer()
    pending.pop(user_id, None)


@dp.callback_query(F.data.startswith("decline:"))
async def decline(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    data = pending.get(user_id)

    if not data:
        await callback.answer("заявка уже обработана")
        return

    await bot.decline_chat_join_request(
        chat_id=data["chat_id"],
        user_id=user_id
    )

    await callback.message.edit_text("❌ пользователь отклонён")
    await callback.answer()
    pending.pop(user_id, None)


@app.route("/", methods=["GET"])
def home():
    return "monster verification bot is running"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        update = Update.model_validate(data)

        asyncio.run(dp.feed_update(bot, update))

        return "ok", 200

    except Exception as e:
        print(f"webhook error: {e}")
        return "error", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
