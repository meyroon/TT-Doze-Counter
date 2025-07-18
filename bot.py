import os
import json
import datetime
import jdatetime
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

# فرمان شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! عدد خود را بفرست تا ثبت شود.\nدستورات:\n/report - گزارش امروز\n/weekly - گزارش هفتگی")

# ذخیره عدد ارسال شده
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_today_date()
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("لطفاً فقط عدد وارد کنید.")
        return

    number = int(text)
    data = load_data()
    if user_id not in data:
        data[user_id] = {}
    if today not in data[user_id]:
        data[user_id][today] = []

    data[user_id][today].append(number)
    save_data(data)
    await update.message.reply_text(f"عدد {number} ذخیره شد.")

# گزارش امروز
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_data()
    today = jdatetime.date.today()
    message_lines = []
    total_all = 0

    for i in range(7):
        day = (today - jdatetime.timedelta(days=i)).isoformat()
        nums = data.get(user_id, {}).get(day, [])
        day_total = sum(nums)
        total_all += day_total
        if nums:
            message_lines.append(f"{day}: {nums} → مجموع: {day_total}")

    if message_lines:
        message = "\n".join(reversed(message_lines)) + f"\n\nمجموع کل هفته: {total_all}"
    else:
        message = "هیچ عددی در هفت روز گذشته ثبت نشده."

    await update.message.reply_text(message)

# اجرای برنامه
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()  # اگر فایل .env داری

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("توکن تلگرام یافت نشد. لطفاً متغیر BOT_TOKEN را تنظیم کن.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("ربات در حال اجراست...")
    app.run_polling()
