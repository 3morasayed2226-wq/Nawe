from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import asyncio, json, os

# ===== Environment Variables =====
TOKEN = os.getenv("7974741054:AAHH5MF5aOyFZe2SgxZC7Q18Dg7FNtEjYxo")
ADMIN_ID = int(os.getenv("7835747296"))
DATA_FILE = "data.json"
# =================================

sending = False

# ---------- Data ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"texts": [], "delay": 1, "group_id": None}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"texts": [], "delay": 1, "group_id": None}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ---------- Helpers ----------
def is_admin(update: Update):
    return update.effective_user and update.effective_user.id == ADMIN_ID

def keyboard():
    return ReplyKeyboardMarkup(
        [
            ["➕ إضافة نص", "📂 إضافة ملف"],
            ["⚡ السرعة", "🎯 الجروب"],
            ["▶️ إرسال", "⛔ إيقاف"],
            ["🗑 مسح النصوص"]
        ],
        resize_keyboard=True
    )

# ---------- start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(
        "🎛 لوحة التحكم",
        reply_markup=keyboard()
    )

# ---------- Messages ----------
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sending
    if not is_admin(update):
        return

    text = update.message.text.strip()

    # أوامر الأزرار
    if text == "➕ إضافة نص":
        context.user_data.clear()
        context.user_data["add_text"] = True
        await update.message.reply_text("✍️ ابعت النص")

    elif text == "📂 إضافة ملف":
        context.user_data.clear()
        context.user_data["add_file"] = True
        await update.message.reply_text("📂 ابعت ملف txt")

    elif text == "⚡ السرعة":
        context.user_data.clear()
        context.user_data["speed"] = True
        await update.message.reply_text("⚡ ابعت السرعة بالثواني")

    elif text == "🎯 الجروب":
        context.user_data.clear()
        context.user_data["group"] = True
        await update.message.reply_text("🎯 ابعت ID الجروب")

    elif text == "▶️ إرسال":
        if sending:
            await update.message.reply_text("⚠️ الإرسال شغال بالفعل")
            return
        if not data["group_id"] or not data["texts"]:
            await update.message.reply_text("❌ لازم تحدد الجروب وتضيف نصوص")
            return
        sending = True
        asyncio.create_task(start_sending(context))
        await update.message.reply_text("▶️ بدأ الإرسال")

    elif text == "⛔ إيقاف":
        sending = False
        await update.message.reply_text("⛔ تم إيقاف الإرسال")

    elif text == "🗑 مسح النصوص":
        data["texts"].clear()
        save_data()
        await update.message.reply_text("🗑 تم مسح كل النصوص")

    # إدخال البيانات
    elif context.user_data.get("add_text"):
        data["texts"].append(text)
        save_data()
        context.user_data.clear()
        await update.message.reply_text(
            f"✅ تم إضافة النص رقم {len(data[ texts ])}"
        )

    elif context.user_data.get("speed") and text.isdigit():
        data["delay"] = float(text)
        save_data()
        context.user_data.clear()
        await update.message.reply_text("⚡ تم حفظ السرعة")

    elif context.user_data.get("group"):
        try:
            data["group_id"] = int(text)
            save_data()
            context.user_data.clear()
            await update.message.reply_text("🎯 تم حفظ الجروب")
        except:
            await update.message.reply_text("❌ ID غير صحيح")

# ---------- File ----------
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    if context.user_data.get("add_file"):
        f = await update.message.document.get_file()
        content = (await f.download_as_bytearray()).decode("utf-8")
        data["texts"].append(content)
        save_data()
        context.user_data.clear()
        await update.message.reply_text(
            f"📂 تم إضافة الملف كنص رقم {len(data[ texts ])}"
        )

# ---------- Sending ----------
async def start_sending(context: ContextTypes.DEFAULT_TYPE):
    global sending
    try:
        for i, block in enumerate(data["texts"], start=1):
            if not sending:
                return

            await context.bot.send_message(
                chat_id=data["group_id"],
                text=f"📌 النص رقم {i}"
            )

            lines = [l for l in block.split("\n") if l.strip()]
            for line in lines:
                if not sending:
                    return
                await context.bot.send_message(
                    chat_id=data["group_id"],
                    text=line
                )
                await asyncio.sleep(data["delay"])
    finally:
        sending = False

# ---------- Main ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()