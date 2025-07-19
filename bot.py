import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from datetime import datetime, timedelta
import os

# راه‌اندازی لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# دیتابیس ساده در حافظه
user_data = {}

# توکن و آدرس Webhook
TOKEN = os.environ.get("TOKEN") or "7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I"
WEBHOOK_URL = "https://tt-doze-counter.onrender.com"

# کمک و شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! برای ثبت مصرف قرص از دستور /add استفاده کن.\nبرای مثال: `/add 2`\nهمچنین:\n/today → گزارش امروز\n/week → گزارش هفتگی\n/help → راهنما", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستورات:\n/add X → ثبت عدد X\n/today → مجموع امروز\n/week → مجموع ۷ روز اخیر")

# ثبت مقدار مصرف
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    if user_id not in user_data:
        user_data[user_id] = {}

    if date_str not in user_data[user_id]:
        user_data[user_id][date_str] = []

    try:
        value = float(context.args[0])
        user_data[user_id][date_str].append((now.isoformat(), value))
        await update.message.reply_text(f"✅ مقدار {value} ثبت شد.")
    except (IndexError, ValueError):
        await update.message.reply_text("فرمت درست نیست. مثال: `/add 1.5`", parse_mode="Markdown")

# گزارش امروز
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    date_str = datetime.now().strftime("%Y-%m-%d")

    total = sum(value for _, value in user_data.get(user_id, {}).get(date_str, []))
    await update.message.reply_text(f"📅 مجموع امروز: {total}")

# گزارش هفته
async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    total = 0
    today = datetime.now()

    for i in range(7):
        day = today - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        daily_entries = user_data.get(user_id, {}).get(date_str, [])
        total += sum(value for _, value in daily_entries)

    await update.message.reply_text(f"🗓 مجموع ۷ روز اخیر: {total}")

# در صورت ارسال پیام غیرمرتبط
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور ناشناخته است. برای راهنما: /help")

# پیکربندی و اجرای ربات
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("week", week))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"{WEBHOOK_URL}/",
    )

if __name__ == "__main__":
    main()
