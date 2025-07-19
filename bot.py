import os
import json
import datetime
import jdatetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from datetime import datetime, time

DATA_FILE = 'data.json'

# بارگذاری داده‌ها از فایل
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# ذخیره داده‌ها در فایل
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# گرفتن تاریخ شمسی به فرمت YYYY-MM-DD
def get_today_date():
    now = datetime.now()
    if now.time() >= time(0, 0):  # ساعت 12 شب به بعد
        today = jdatetime.date.today()
    else:
        today = jdatetime.date.today() - jdatetime.timedelta(days=1)
    return today.isoformat()

# گرفتن تاریخ شروع هفته (شنبه)
def get_start_of_week():
    today = jdatetime.date.today()
    start_of_week = today - jdatetime.timedelta(days=today.weekday())  # گرفتن تاریخ شنبه این هفته
    return start_of_week.isoformat()

# گرفتن تاریخ شروع ماه (اول ماه)
def get_start_of_month():
    today = jdatetime.date.today()
    start_of_month = today.replace(day=1).isoformat()
    return start_of_month

# گرفتن تاریخ پایان ماه (آخر ماه)
def get_end_of_month():
    today = jdatetime.date.today()
    end_of_month = (today.replace(day=1) + jdatetime.timedelta(days=32)).replace(day=1) - jdatetime.timedelta(days=1)
    return end_of_month.isoformat()

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! برای ثبت مصرف روزانه‌تان، عدد مورد نظر را ارسال کنید.")

# گزارش روزانه
async def report_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_today_date()
    data = load_data()
    numbers = data.get(user_id, {}).get(today, [])

    if numbers:
        total = sum(numbers)
        await update.message.reply_text(f"مقادیر امروز ({today}): {numbers}\nمجموع: {total}")
    else:
        await update.message.reply_text("هنوز عددی برای امروز ثبت نکردی.")

# گزارش هفتگی
async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_data()
    start_of_week = get_start_of_week()
    end_of_week = jdatetime.date.fromisoformat(start_of_week) + jdatetime.timedelta(days=6)

    message_lines = []
    total_all = 0

    for i in range(7):
        day = (start_of_week + jdatetime.timedelta(days=i)).isoformat()
        nums = data.get(user_id, {}).get(day, [])
        day_total = sum(nums)
        total_all += day_total
        if nums:
            message_lines.append(f"{day}: {nums} → مجموع: {day_total}")

    if message_lines:
        message = "\n".join(message_lines) + f"\n\nمجموع کل هفته ({start_of_week} - {end_of_week}): {total_all}"
        await update.message.reply_text(f"گزارش هفته: \n{message}")
    else:
        await update.message.reply_text("هیچ عددی در هفته جاری ثبت نشده.")

# گزارش ماهانه
async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_data()
    today = jdatetime.date.today()
    start_of_month = get_start_of_month()
    end_of_month = get_end_of_month()

    message_lines = []
    total_all = 0

    for day in range(1, today.day + 1):
        day_str = (today.replace(day=day)).isoformat()
        nums = data.get(user_id, {}).get(day_str, [])
        day_total = sum(nums)
        total_all += day_total
        if nums:
            message_lines.append(f"{day_str}: {nums} → مجموع: {day_total}")

    message = f"گزارش مصرف ماهانه ({start_of_month} - {end_of_month}):\n" + "\n".join(message_lines) + f"\n\nمجموع کل ماه: {total_all}"
    await update.message.reply_text(message)

# ریست روزانه
async def reset_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_today_date()
    data = load_data()

    if user_id in data and today in data[user_id]:
        del data[user_id][today]
        save_data(data)
        await update.message.reply_text("✅ داده‌های امروز ریست شد.")
    else:
        await update.message.reply_text("هیچ داده‌ای برای امروز ثبت نشده است.")

# ریست هفتگی
async def reset_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_data()
    start_of_week = get_start_of_week()

    if user_id in data:
        keys_to_delete = [day for day in data[user_id] if jdatetime.date.fromisoformat(day) >= jdatetime.date.fromisoformat(start_of_week)]
        for key in keys_to_delete:
            del data[user_id][key]
        save_data(data)
        await update.message.reply_text("✅ داده‌های هفتگی ریست شد.")
    else:
        await update.message.reply_text("هیچ داده‌ای برای هفته جاری ثبت نشده است.")

# اجرای برنامه با Webhook
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()  # اگر فایل .env داری

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("توکن تلگرام یافت نشد. لطفاً متغیر BOT_TOKEN را تنظیم کن.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))  # اضافه کردن دستور /help
    app.add_handler(CommandHandler("report_day", report_day))  # دستور گزارش روزانه
    app.add_handler(CommandHandler("report_week", report_week))  # دستور گزارش هفتگی
    app.add_handler(CommandHandler("report_month", report_month))  # دستور گزارش ماهانه
    app.add_handler(CommandHandler("reset_day", reset_day))  # دستور ریست روزانه
    app.add_handler(CommandHandler("reset_week", reset_week))  # دستور ریست هفتگی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("ربات در حال اجراست...")
    app.run_webhook(
        listen="0.0.0.0",  # اجازه می‌دهد تا درخواست‌ها از همه IP‌ها بیاید
        port=443,  # پورت 443 برای HTTPS
        url_path=TOKEN,  # توکن ربات به‌عنوان مسیر
        webhook_url=f"https://tt-doze-counter.onrender.com/{TOKEN}",  # URL اختصاصی Render شما
    )
