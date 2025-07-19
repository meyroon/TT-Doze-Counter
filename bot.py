from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os

# متغیرهای محیطی
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # آدرس کامل، مثلا https://your-app-name.onrender.com/webhook

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# دیتابیس ساده
from datetime import datetime
data_store = {}

def get_persian_date():
    from persiantools.jdatetime import JalaliDate
    return str(JalaliDate.today())

async def save_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کن.")
        return

    user_id = update.effective_user.id
    date = get_persian_date()
    data_store.setdefault(user_id, {}).setdefault(date, []).append(value)

    await update.message.reply_text(f"عدد {value} ذخیره شد.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    date = get_persian_date()
    numbers = data_store.get(user_id, {}).get(date, [])

    if not numbers:
        await update.message.reply_text("هیچ عددی برای امروز ثبت نشده.")
        return

    total = sum(numbers)
    await update.message.reply_text(f"مقادیر امروز ({date}): {numbers}\nمجموع: {total}")

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_number))
application.add_handler(CommandHandler("report", report))

# مسیر دریافت پیام‌های تلگرام
@app.post('/webhook')
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return 'ok'

# ست کردن webhook در اولین اجرا
@app.before_first_request
def set_webhook():
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(application.bot.set_webhook(url=WEBHOOK_URL))

if __name__ == "__main__":
    app.run(port=10000)
