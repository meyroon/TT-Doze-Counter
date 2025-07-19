import json
import datetime
from persiantools.jdatetime import JalaliDate
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

DATA_FILE = "data.json"

# بارگذاری داده‌ها از فایل
try:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("افزودن مقدار", callback_data="add"),
            InlineKeyboardButton("گزارش امروز", callback_data="report_day"),
        ],
        [
            InlineKeyboardButton("گزارش هفتگی", callback_data="report_week"),
            InlineKeyboardButton("گزارش ماهانه", callback_data="report_month"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("به بات ثبت مصرف دارو خوش آمدید! 👋", reply_markup=reply_markup)

# ثبت مقدار
async def add_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("لطفاً مقدار مصرف قرص را وارد کنید (مثلاً ۱ یا ۲):")
    context.user_data["awaiting_value"] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_value"):
        try:
            value = int(update.message.text)
            user_id = str(update.effective_user.id)
            today = str(datetime.date.today())
            user_data = data.setdefault(user_id, [])
            user_data.append({"date": today, "value": value})
            save_data()
            await update.message.reply_text(f"✅ {value} قرص ثبت شد.")
        except ValueError:
            await update.message.reply_text("لطفاً فقط یک عدد وارد کنید.")
        context.user_data["awaiting_value"] = False

# گزارش روزانه
async def report_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today = datetime.date.today()
    today_jalali = JalaliDate(today)
    user_data = data.get(user_id, [])
    total = sum(entry["value"] for entry in user_data if entry["date"] == str(today))

    message = (
        f"📅 گزارش روزانه\n"
        f"تاریخ: {today_jalali}\n\n"
        f"📊 مجموع مصرف امروز: {total} قرص"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message)
    else:
        await update.message.reply_text(message)

# گزارش هفتگی
def get_start_of_week():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday() + 2 if today.weekday() != 5 else 6)
    return start

async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today = datetime.date.today()
    start_of_week = get_start_of_week()
    today_jalali = JalaliDate(today)
    start_jalali = JalaliDate(start_of_week)
    user_data = data.get(user_id, [])
    total = 0
    for entry in user_data:
        entry_date = datetime.datetime.strptime(entry["date"], "%Y-%m-%d").date()
        if start_of_week <= entry_date <= today:
            total += entry["value"]

    message = (
        f"📅 گزارش هفتگی\n"
        f"از تاریخ: {start_jalali}\n"
        f"تا تاریخ: {today_jalali}\n\n"
        f"📊 مجموع مصرف ثبت‌شده در این هفته: {total} قرص"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message)
    else:
        await update.message.reply_text(message)

# گزارش ماهانه
async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today = JalaliDate.today()
    start_of_month = JalaliDate(today.year, today.month, 1)
    user_data = data.get(user_id, [])
    total = 0
    for entry in user_data:
        entry_date = datetime.datetime.strptime(entry["date"], "%Y-%m-%d").date()
        entry_jalali = JalaliDate(entry_date)
        if start_of_month <= entry_jalali <= today:
            total += entry["value"]

    message = (
        f"📅 گزارش ماهانه\n"
        f"از تاریخ: {start_of_month}\n"
        f"تا تاریخ: {today}\n\n"
        f"📊 مجموع مصرف ثبت‌شده در این ماه: {total} قرص"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message)
    else:
        await update.message.reply_text(message)

# مدیریت دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "add":
        await add_entry(update, context)
    elif query.data == "report_day":
        await report_day(update, context)
    elif query.data == "report_week":
        await report_week(update, context)
    elif query.data == "report_month":
        await report_month(update, context)

# اجرای بات
if __name__ == "__main__":
    import asyncio

    TOKEN = "7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I"
    WEBHOOK_URL = "https://tt-doze-counter.onrender.com"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")

    app.run_webhook(
        listen="0.0.0.0",  # Listen on all IPs
        port=int(os.environ.get("PORT", 8080)),  # Use port 8080 or environment variable
        url_path=TOKEN,  # Use the token as the webhook path
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",  # Webhook URL with token
    )
