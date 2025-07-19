import os
import json
import datetime
import jdatetime
from decimal import Decimal
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

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
    return jdatetime.date.today().isoformat()

# گرفتن تاریخ شروع هفته (شنبه)
def get_start_of_week():
    today = jdatetime.date.today()
    start_of_week = today - jdatetime.timedelta(days=today.weekday() + 1)  # شنبه
    return start_of_week.isoformat()

# دستور /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "دستورات ربات:\n\n"
        "/start - شروع\n"
        "/report_day - گزارش روزانه\n"
        "/report_week - گزارش هفتگی\n"
        "/report_month - گزارش ماهانه\n"
        "/reset_day - ریست کردن داده‌های روزانه\n"
        "/reset_week - ریست کردن داده‌های هفتگی\n"
        "/reset_month - ریست کردن داده‌های ماهانه\n"
        "/help - نمایش این راهنما"
    )
    await update.message.reply_text(help_text)

# فرمان شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! عدد خود را بفرست تا ثبت شود.\nدستورات:\n/report_day - گزارش روزانه\n/report_week - گزارش هفتگی\n/report_month - گزارش ماهانه\n/help - برای راهنما")

# ذخیره عدد ارسال شده
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_today_date()
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
    start_of_week = get_start_of_week()  # تاریخ شروع هفته
    today = jdatetime.date.today()

    # محاسبه تاریخ پایان هفته (جمعه)
    week_end = today - jdatetime.timedelta(days=(today.weekday() + 1) % 7)  # جمعه آخر هفته

    total_week = Decimal("0")
    message_lines = []
    
    for day in list(data.get(user_id, {}).keys()):
        date_obj = jdatetime.date.fromisoformat(day)
        if jdatetime.date.fromisoformat(start_of_week) <= date_obj <= today:
            nums = data[user_id].get(day, [])
            total_day = sum(nums)
            total_week += Decimal(str(total_day))
            message_lines.append(f"{day}: {nums} → مجموع: {total_day}")

    if message_lines:
        message = "\n".join(message_lines) + f"\n\nمجموع مصرف هفته از {start_of_week} تا {week_end}: {total_week}"
        await update.message.reply_text(f"📊 گزارش مصرف هفته از {start_of_week} تا {week_end}:\n{message}")
    else:
        await update.message.reply_text(f"ℹ️ هیچ مصرفی در هفته از {start_of_week} تا {week_end} ثبت نشده است.")

    # ریست کردن هفته جدید
    await update.message.reply_text(f"وارد هفته جدید شدیم! داده‌های هفته گذشته پاک شد.")

# گزارش ماهانه
async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_data()
    
    # محاسبه تاریخ اول ماه جاری شمسی
    today = jdatetime.date.today()
    first_of_month = today.replace(day=1).isoformat()  # تاریخ اول ماه
    last_of_month = (today.replace(day=1) + jdatetime.timedelta(days=32)).replace(day=1) - jdatetime.timedelta(days=1)  # آخرین روز ماه
    
    total_month = Decimal("0")
    message_lines = []
    
    # محاسبه مصرف از اول ماه تا امروز
    for day in list(data.get(user_id, {}).keys()):
        if first_of_month <= day <= today.isoformat():
            nums = data[user_id].get(day, [])
            total_day = sum(nums)
            total_month += Decimal(str(total_day))
            message_lines.append(f"{day}: {nums} → مجموع: {total_day}")

    # نمایش گزارش
    if message_lines:
        message = "\n".join(message_lines) + f"\n\nمجموع مصرف ماه جاری از {first_of_month} تا {today.isoformat()}: {total_month}"
        await update.message.reply_text(f"📊 گزارش مصرف ماه از {first_of_month} تا {today.isoformat()}:\n{message}")
    else:
        await update.message.reply_text(f"ℹ️ هیچ مصرفی در ماه جاری ({first_of_month} تا {today.isoformat()}) ثبت نشده است.")

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

# ریست ماهانه
async def reset_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_data()
    today = jdatetime.date.today()
    first_of_month = today.replace(day=1).isoformat()  # تاریخ اول ماه

    if user_id in data:
        keys_to_delete = [day for day in data[user_id] if day >= first_of_month]
        for key in keys_to_delete:
            del data[user_id][key]
        save_data(data)
        await update.message.reply_text(f"✅ داده‌های ماهانه از {first_of_month} ریست شد.")
    else:
        await update.message.reply_text("هیچ داده‌ای برای ماه جاری ثبت نشده است.")

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
    app.add_handler(CommandHandler("reset_month", reset_month))  # دستور ریست ماهانه
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("ربات در حال اجراست...")
    app.run_webhook(
        listen="0.0.0.0",  # اجازه می‌دهد تا درخواست‌ها از همه IP‌ها بیاید
        port=443,  # پورت 443 برای HTTPS
        url_path=TOKEN,  # توکن ربات به‌عنوان مسیر
        webhook_url=f"https://tt-doze-counter.onrender.com/{TOKEN}",  # URL اختصاصی Render شما
    )
