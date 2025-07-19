import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from persiantools.jdatetime import JalaliDate
from datetime import datetime, timedelta

TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

user_data = {}

def today_key():
    return JalaliDate.today().isoformat()

def week_keys():
    today = JalaliDate.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(7)]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! عدد مصرف قرص رو بفرست.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    try:
        number = int(text)
        today = today_key()
        user_data.setdefault(user_id, {}).setdefault(today, []).append(number)
        await update.message.reply_text(f"ثبت شد: {number}")
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد بفرست.")

async def report_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    today = today_key()
    data = user_data.get(user_id, {}).get(today, [])
    total = sum(data)
    await update.message.reply_text(f"مجموع امروز: {total} (ثبت‌شده‌ها: {data})")

async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    messages = []
    for key in reversed(week_keys()):
        data = user_data.get(user_id, {}).get(key, [])
        total = sum(data)
        messages.append(f"{key}: {total} ({data})")
    await update.message.reply_text("\n".join(messages))

telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("امروز", report_today))
telegram_app.add_handler(CommandHandler("هفته", report_week))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    await telegram_app.update_queue.put(Update.de_json(request.get_json(force=True), telegram_app.bot))
    return "ok"

if __name__ == "__main__":
    import asyncio
    import logging
    logging.basicConfig(level=logging.INFO)

    async def run():
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            url_path=TOKEN,
            webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"
        )
        await telegram_app.updater.idle()

    asyncio.run(run())
