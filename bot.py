import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

TOKEN = "BOT_TOKEN"
ADMIN_ID = 123456789

bot = Bot(TOKEN)
dp = Dispatcher()

# ================= DATABASE =================
async def db_init():
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS buttons(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            photo TEXT,
            text TEXT
        )
        """)
        await db.commit()

# ================= KEYBOARD =================
async def make_keyboard():
    buttons = []
    async with aiosqlite.connect("db.sqlite") as db:
        async with db.execute("SELECT id,name FROM buttons") as cur:
            rows = await cur.fetchall()

    for row in rows:
        buttons.append([InlineKeyboardButton(
            text=row[1],
            callback_data=f"show_{row[0]}"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ================= START =================
@dp.message(Command("start"))
async def start(msg: Message):
    text = """👋 Assalomu Aleykum

👇 Marhamat o'zingizga yoqgan Mashxur PUBGER ni tanlang:"""

    kb = await make_keyboard()

    if kb.inline_keyboard:
        await msg.answer(text, reply_markup=kb)
    else:
        await msg.answer(text + "\n\n(Hozircha tugma yo‘q)")

# ================= BUTTON CLICK =================
@dp.callback_query(F.data.startswith("show_"))
async def show(call: CallbackQuery):
    btn_id = int(call.data.split("_")[1])

    async with aiosqlite.connect("db.sqlite") as db:
        async with db.execute(
            "SELECT photo,text FROM buttons WHERE id=?",
            (btn_id,)
        ) as cur:
            data = await cur.fetchone()

    if data:
        photo, text = data
        await call.message.answer_photo(photo, caption=text)

    await call.answer()

# ================= ADMIN ADD =================
admin_state = {}

@dp.message(Command("admin"))
async def admin_start(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    admin_state[msg.from_user.id] = {"step": "name"}
    await msg.answer("🛠 Tugma nomini yuboring:")

@dp.message()
async def admin_flow(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    state = admin_state.get(msg.from_user.id)
    if not state:
        return

    # NAME
    if state["step"] == "name":
        state["name"] = msg.text
        state["step"] = "photo"
        await msg.answer("📷 Rasm yuboring:")
        return

    # PHOTO
    if state["step"] == "photo":
        if not msg.photo:
            await msg.answer("❌ Rasm yuboring!")
            return

        state["photo"] = msg.photo[-1].file_id
        state["step"] = "text"
        await msg.answer("📝 Matn yuboring:")
        return

    # TEXT
    if state["step"] == "text":
        state["text"] = msg.text

        async with aiosqlite.connect("db.sqlite") as db:
            await db.execute(
                "INSERT INTO buttons(name,photo,text) VALUES(?,?,?)",
                (state["name"], state["photo"], state["text"])
            )
            await db.commit()

        admin_state.pop(msg.from_user.id)
        await msg.answer("✅ Tugma qo‘shildi!")

# ================= RUN =================
async def main():
    await db_init()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
