import os
from datetime import datetime, timedelta
from collections import defaultdict

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    filters
)

# تنظیمات توکن و آدرس وب‌هوک
TOKEN = "7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I"
WEBHOOK_URL = "https://tt-doze-counter.onrender.com"

# پایگاه داده ساده در حافظه
user_data = defaultdict(list)

# دستور شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! دوز امروزت رو بنویس. مثلاً: 5")

# ذخیره دوز جدید
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dose = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد بنویس")
        return

    user_id = update.effective_user.id
    now = datetime.now()
    user_data[user_id].append((now, dose))
    await update.message.reply_text(f"دوز {dose} ثبت شد ✅")

# گزارش دوز امروز
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    total = sum(
        dose for dt, dose in user_data[user_id]
        if dt.date() == now.date()
    )
    await update.message.reply_text(f"دوز مصرفی امروز: {total}")

# گزارش هفتگی
async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    start_of_week = now - timedelta(days=6)
    total = sum(
        dose for dt, dose in user_data[user_id]
        if start_of_week.date() <= dt.date() <= now.date()
    )
    await update.message.reply_text(f"دوز مجموع در هفته اخیر: {total}")

# راه‌اندازی بات
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    # ست‌کردن وب‌هوک
    await app.bot.set_webhook(url=WEBHOOK_URL)
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
