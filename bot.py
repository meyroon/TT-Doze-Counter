import logging
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, timedelta
import json
import os
import pytz
from collections import defaultdict
from flask import Flask, request

# تنظیم منطقه زمانی
IR_TZ = pytz.timezone("Asia/Tehran")

# تنظیمات ورود اطلاعات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# فایل ذخیره اطلاعات
DATA_FILE = "data.json"

# بارگذاری داده‌ها
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# ذخیره داده‌ها
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)

# دریافت تاریخ امروز به وقت ایران
def get_today():
    return datetime.now(IR_TZ).strftime("%Y-%m-%d")

# دریافت ابتدای هفته (شنبه)
def get_week_start(date_str=None):
    today = datetime.now(IR_TZ) if not date_str else datetime.strptime(date_str, "%Y-%m-%d")
    today = today.astimezone(IR_TZ)
    week_start = today - timedelta(days=today.weekday() + 1 if today.weekday() < 6 else 0)
    return week_start.strftime("%Y-%m-%d")

# دریافت ابتدای و انتهای ماه
def get_month_range():
    now = datetime.now(IR_TZ)
    first_day = now.replace(day=1).strftime("%Y-%m-%d")
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    last_day = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
    return first_day, last_day

# افزودن مقدار مصرف
async def add_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    text = update.message.text.replace(",", ".").strip()

    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد مثبت وارد کنید. مثلاً 1 یا 0.5")
        return

    today = get_today()
    if user_id not in data:
        data[user_id] = {}
    if today not in data[user_id]:
        data[user_id][today] = 0.0

    data[user_id][today] += amount
    save_data(data)
    await update.message.reply_text(f"✔️ ثبت شد. مجموع امروز: {data[user_id][today]} عدد")

# گزارش روزانه
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    today = get_today()
    amount = data.get(user_id, {}).get(today, 0.0)
    await update.message.reply_text(f"📊 مجموع مصرف امروز ({today}): {amount} عدد")

# گزارش هفتگی
async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    week_start = get_week_start()
    week_total = 0.0

    for date_str, value in data.get(user_id, {}).items():
        if date_str >= week_start:
            week_total += value

    await update.message.reply_text(f"📅 مصرف هفتگی از شنبه ({week_start}) تاکنون: {week_total} عدد")

# گزارش ماهانه
async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    start, end = get_month_range()
    total = 0.0

    for date_str, value in data.get(user_id, {}).items():
        if start <= date_str <= end:
            total += value

    await update.message.reply_text(f"🗓 مصرف ماهانه از {start} تا {end}: {total} عدد")

# ریست روزانه
async def reset_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    today = get_today()
    if user_id in data and today in data[user_id]:
        del data[user_id][today]
        save_data(data)
        await update.message.reply_text("🔄 مصرف امروز ریست شد.")
    else:
        await update.message.reply_text("هیچ مصرفی برای امروز ثبت نشده بود.")

# ریست دستی هفتگی
async def reset_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    week_start = get_week_start()

    removed = 0
    for date in list(data.get(user_id, {}).keys()):
        if date >= week_start:
            del data[user_id][date]
            removed += 1

    save_data(data)
    await update.message.reply_text(f"✅ ریست هفتگی انجام شد. {removed} روز پاک شد.")

# ریست خودکار هفته در روز شنبه
async def check_weekly_reset(application):
    data = load_data()
    now = datetime.now(IR_TZ)
    if now.weekday() == 5:  # شنبه
        for user_id in data.keys():
            week_start = get_week_start()
            weekly_total = 0.0
            for date_str in list(data[user_id].keys()):
                if date_str < week_start:
                    weekly_total += data[user_id][date_str]
                    del data[user_id][date_str]
            if weekly_total > 0:
                await application.bot.send_message(
                    chat_id=user_id,
                    text=f"📤 هفته گذشته به پایان رسید.\nمجموع مصرف هفته گذشته: {weekly_total} عدد\nشروع هفته جدید مبارک!"
                )
        save_data(data)

# پیام راهنما
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📘 راهنمای استفاده:\n"
        "/report - گزارش امروز\n"
        "/report_week - گزارش هفتگی\n"
        "/report_month - گزارش ماهانه\n"
        "/reset_day - ریست مصرف امروز\n"
        "/reset_week - ریست مصرف این هفته\n"
        "/help - نمایش این راهنما\n\n"
        "همچنین می‌توانید عدد مصرف را مستقیماً ارسال کنید."
    )
    await update.message.reply_text(text)

# تنظیم منو
async def set_main_menu(application):
    commands = [
        BotCommand("help", "راهنمای دستورات"),
        BotCommand("report", "گزارش امروز"),
        BotCommand("report_week", "گزارش هفتگی"),
        BotCommand("report_month", "گزارش ماهانه"),
        BotCommand("reset_day", "ریست روزانه"),
        BotCommand("reset_week", "ریست هفتگی")
    ]
    await application.bot.set_my_commands(commands)

# ساخت اپلیکیشن
TOKEN = "7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I"
WEBHOOK_URL = "https://tt-doze-counter.onrender.com"

application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", help_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("report", report))
application.add_handler(CommandHandler("report_week", report_week))
application.add_handler(CommandHandler("report_month", report_month))
application.add_handler(CommandHandler("reset_day", reset_day))
application.add_handler(CommandHandler("reset_week", reset_week))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), add_entry))

# Flask app (برای Render)
flask_app = Flask(__name__)

@flask_app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK"

@flask_app.route("/", methods=["GET"])
def index():
    return "ربات فعال است."

if __name__ == "__main__":
    import asyncio

    async def main():
        await set_main_menu(application)
        await check_weekly_reset(application)
        await application.bot.set_webhook(WEBHOOK_URL)
        flask_app.run(host="0.0.0.0", port=8080)

    asyncio.run(main())
