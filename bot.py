import os
import json
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN", "7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I")
WEBHOOK_URL = "https://tt-doze-counter.onrender.com"

DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_user_file(user_id):
    return os.path.join(DATA_DIR, f"{user_id}.json")

def load_user_data(user_id):
    file_path = get_user_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    else:
        return {}

def save_user_data(user_id, data):
    with open(get_user_file(user_id), "w") as f:
        json.dump(data, f)

def add_dose(user_id, amount):
    data = load_user_data(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M")
    data.setdefault(today, []).append({"time": now, "amount": amount})
    save_user_data(user_id, data)

def get_daily_report(user_id, date_str=None):
    data = load_user_data(user_id)
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    entries = data.get(date_str, [])
    total = sum(entry["amount"] for entry in entries)
    details = "\n".join([f"⏰ {entry['time']} ➤ {entry['amount']}" for entry in entries]) or "هیچ موردی ثبت نشده"
    return f"📅 گزارش روز {date_str}:\n{details}\n\n🔢 مجموع: {total}"

def get_start_of_week():
    today = datetime.now()
    start = today - timedelta(days=(today.weekday() + 1) % 7)  # Saturday
    return start.date()

def get_weekly_report(user_id):
    data = load_user_data(user_id)
    start = get_start_of_week()
    end = start + timedelta(days=6)
    total_week = 0
    daily_reports = []

    for i in range(7):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        entries = data.get(day, [])
        total = sum(entry["amount"] for entry in entries)
        if entries:
            details = "\n".join([f"{entry['time']} ➤ {entry['amount']}" for entry in entries])
            report = f"📆 {day}:\n{details}\n🧮 مجموع: {total}"
        else:
            report = f"📆 {day}: هیچ موردی ثبت نشده"
        daily_reports.append(report)
        total_week += total

    summary = "\n\n".join(daily_reports)
    return f"📊 گزارش هفتگی ({start} تا {end}):\n\n{summary}\n\n🔁 مجموع کل هفته: {total_week}"

# دستورات ربات

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! مقدار مصرفت رو با فرستادن عدد وارد کن.\n"
        "با /daily گزارش امروز رو بگیر.\n"
        "با /weekly گزارش هفتگی رو ببین."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.isdigit():
        user_id = str(update.message.from_user.id)
        amount = int(text)
        add_dose(user_id, amount)
        await update.message.reply_text(f"✔️ {amount} ثبت شد.")
    else:
        await update.message.reply_text("لطفاً فقط عدد بفرست.")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    report = get_daily_report(user_id)
    await update.message.reply_text(report)

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    report = get_weekly_report(user_id)
    await update.message.reply_text(report)

# تنظیمات اپلیکیشن

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("daily", daily))
app.add_handler(CommandHandler("weekly", weekly))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# راه‌اندازی webhook با Flask

flask_app = Flask(__name__)

@flask_app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

@flask_app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.update_queue.put_nowait(update)
    return "ok"

async def set_webhook():
    await app.bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    import asyncio
    asyncio.run(set_webhook())
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )
