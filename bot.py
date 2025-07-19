import os
import json
import datetime
from decimal import Decimal
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import jdatetime

# فایل داده‌ها
DATA_FILE = "data.json"

# بارگذاری داده‌ها از فایل
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# ذخیره داده‌ها در فایل
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# دریافت تاریخ امروز به شمسی
def get_today():
    return jdatetime.date.today().isoformat()

# دریافت شروع هفته (شنبه)
def get_week_start():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=(today.weekday() + 1) % 7)  # شنبه به عنوان اول هفته
    return start.isoformat()

# دریافت محدوده ماه (اول ماه و آخر ماه)
def get_month_range():
    today = jdatetime.date.today()
    first = today.replace(day=1)
    if today.month == 12:
        last = today.replace(year=today.year + 1, month=1, day=1) - datetime.timedelta(days=1)
    else:
        last = today.replace(month=today.month + 1, day=1) - datetime.timedelta(days=1)
    return first.isoformat(), last.isoformat()

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! عدد مصرف را وارد کنید یا از دستورات استفاده کنید. برای راهنما، دستور /help را بزنید.")

# دستور /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - شروع\n"
        "/report_day - گزارش مصرف امروز\n"
        "/report_week - گزارش مصرف این هفته\n"
        "/report_month - گزارش مصرف این ماه\n"
        "/reset_day - ریست اطلاعات امروز\n"
        "/reset_week - ریست اطلاعات این هفته\n"
        "/reset_month - ریست اطلاعات این ماه\n"
        "/help - راهنمای دستورات"
    )

# دستور /reset_day
async def reset_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    today = get_today()
    if user_id in data and today in data[user_id]:
        del data[user_id][today]
        save_data(data)
        await update.message.reply_text("✅ مصرف امروز پاک شد.")
    else:
        await update.message.reply_text("ℹ️ مصرفی برای امروز ثبت نشده بود.")

# دستور /reset_week
async def reset_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    week_start = get_week_start()
    today = datetime.date.today()

    if user_id in data:
        for day in list(data[user_id].keys()):
            date_obj = datetime.date.fromisoformat(day)
            if datetime.date.fromisoformat(week_start) <= date_obj <= today:
                del data[user_id][day]
        save_data(data)
        await update.message.reply_text("✅ مصرف این هفته پاک شد.")
    else:
        await update.message.reply_text("ℹ️ داده‌ای برای پاک کردن نبود.")

# دستور /reset_month
async def reset_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    first_of_month, _ = get_month_range()

    if user_id in data:
        for day in list(data[user_id].keys()):
            if day < first_of_month:
                del data[user_id][day]
        save_data(data)
        await update.message.reply_text("✅ مصرف این ماه پاک شد.")
    else:
        await update.message.reply_text("ℹ️ داده‌ای برای پاک کردن نبود.")

# دستور /report_day
async def report_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    today = get_today()

    total = Decimal("0")
    if user_id in data and today in data[user_id]:
        total = Decimal(str(sum(data[user_id][today])))

    await update.message.reply_text(f"📊 گزارش مصرف امروز ({today}):\n🔢 مجموع مصرف: {total} عدد")

# دستور /report_week
async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    week_start = get_week_start()

    total_week = Decimal("0")
    message_lines = []
    for day in list(data.get(user_id, {}).keys()):
        date_obj = datetime.date.fromisoformat(day)
        if datetime.date.fromisoformat(week_start) <= date_obj <= datetime.date.today():
            nums = data[user_id].get(day, [])
            total_day = sum(nums)
            total_week += Decimal(str(total_day))
            message_lines.append(f"{day}: {nums} → مجموع: {total_day}")

    if message_lines:
        message = "\n".join(message_lines) + f"\n\nمجموع مصرف هفته جاری: {total_week}"
        await update.message.reply_text(f"📊 گزارش مصرف این هفته:\n{message}")
    else:
        await update.message.reply_text("ℹ️ هیچ مصرفی در این هفته ثبت نشده است.")

# دستور /report_month
async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    first_of_month, last_of_month = get_month_range()

    total_month = Decimal("0")
    message_lines = []
    for day in list(data.get(user_id, {}).keys()):
        if first_of_month <= day <= last_of_month:
            nums = data[user_id].get(day, [])
            total_day = sum(nums)
            total_month += Decimal(str(total_day))
            message_lines.append(f"{day}: {nums} → مجموع: {total_day}")

    if message_lines:
        message = "\n".join(message_lines) + f"\n\nمجموع مصرف ماه جاری: {total_month}"
        await update.message.reply_text(f"📊 گزارش مصرف این ماه:\n{message}")
    else:
        await update.message.reply_text("ℹ️ هیچ مصرفی در این ماه ثبت نشده است.")

# ذخیره عدد وارد شده
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today = get_today()
    text = update.message.text.strip()

    try:
        number = float(text)  # برای پذیرش اعداد اعشاری
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد وارد کنید.")
        return

    data = load_data()
    if user_id not in data:
        data[user_id] = {}
    if today not in data[user_id]:
        data[user_id][today] = []

    data[user_id][today].append(number)
    save_data(data)
    await update.message.reply_text(f"عدد {number} ذخیره شد.")

# اجرای برنامه با Webhook
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()  # اگر فایل .env داری

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("توکن تلگرام یافت نشد. لطفاً متغیر BOT_TOKEN را تنظیم کن.")

    app = ApplicationBuilder().token(TOKEN).build()

    # دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset_day", reset_day))
    app.add_handler(CommandHandler("reset_week", reset_week))
    app.add_handler(CommandHandler("reset_month", reset_month))
    app.add_handler(CommandHandler("report_day", report_day))
    app.add_handler(CommandHandler("report_week", report_week))
    app.add_handler(CommandHandler("report_month", report_month))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        url_path=TOKEN,
        webhook_url=f"https://tt-doze-counter.onrender.com/{TOKEN}",
    )
