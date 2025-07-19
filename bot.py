import os
import json
import datetime
import jdatetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# ساخت دکمه‌ها برای نمایش مجدد گزینه‌ها
def get_keyboard():
    return [
        [InlineKeyboardButton("گزارش روزانه", callback_data="report_day")],
        [InlineKeyboardButton("گزارش هفتگی", callback_data="report_week")],
        [InlineKeyboardButton("گزارش ماهانه", callback_data="report_month")],
        [InlineKeyboardButton("ریست روزانه", callback_data="reset_day")],
    ]

# ارسال مجدد دکمه‌ها بعد از هر پاسخ
async def show_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup)

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لطفاً یکی از گزینه‌ها را انتخاب کنید:")
    await show_options(update, context)

# گزارش روزانه
async def report_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_today_date()
    data = load_data()
    numbers = data.get(user_id, {}).get(today, [])
    total = sum(numbers) if numbers else 0
    await update.message.reply_text(f"گزارش امروز ({today}): {numbers}\nمجموع: {total}")
    await show_options(update, context)

# گزارش هفتگی
async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_today_date()
    data = load_data()
    message_lines = []
    total_all = 0

    # تاریخ شروع هفته و پایان هفته
    start_of_week = get_start_of_week()

    for i in range(7):
        day = (start_of_week - jdatetime.timedelta(days=i)).isoformat()
        nums = data.get(user_id, {}).get(day, [])
        day_total = sum(nums)
        total_all += day_total
        if nums:
            message_lines.append(f"{day}: {nums} → مجموع: {day_total}")

    message = "\n".join(reversed(message_lines)) + f"\n\nمجموع کل هفته: {total_all}"
    await update.message.reply_text(f"گزارش هفته از {start_of_week}:\n{message}")
    await show_options(update, context)

# گزارش ماهانه
async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_data()
    today = jdatetime.date.today()
    start_of_month = today.replace(day=1).isoformat()

    # محاسبه تعداد مصرف تا پایان ماه
    message_lines = []
    total_all = 0

    for day in range(1, (today.day + 1)):
        day_str = (today.replace(day=day)).isoformat()
        nums = data.get(user_id, {}).get(day_str, [])
        day_total = sum(nums)
        total_all += day_total
        if nums:
            message_lines.append(f"{day_str}: {nums} → مجموع: {day_total}")

    message = f"گزارش مصرف ماهانه از {start_of_month} تا {today}: \n" + "\n".join(message_lines) + f"\n\nمجموع کل ماه: {total_all}"
    await update.message.reply_text(message)
    await show_options(update, context)

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
    await show_options(update, context)

# مدیریت پیام‌ها
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
    await show_options(update, context)

# برای شروع هر هفته از روز شنبه
def get_start_of_week():
    today = jdatetime.date.today()
    return today - jdatetime.timedelta(days=today.weekday() + 1)

# اجرا
if __name__ == "__main__":
    TOKEN = "7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report_day", report_day))
    app.add_handler(CommandHandler("report_week", report_week))
    app.add_handler(CommandHandler("report_month", report_month))
    app.add_handler(CommandHandler("reset_day", reset_day))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("ربات در حال اجراست...")
    app.run_polling()
