import os
import json
import datetime
from decimal import Decimal, InvalidOperation
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = "7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I"
WEBHOOK_URL = "https://tt-doze-counter.onrender.com"

DATA_FILE = "data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_today():
    return datetime.date.today().isoformat()


def get_week_start():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=(today.weekday() + 1) % 7)  # شنبه به عنوان اول هفته
    return start.isoformat()


def get_month_range():
    today = datetime.date.today()
    first = today.replace(day=1)
    if today.month == 12:
        last = today.replace(year=today.year + 1, month=1, day=1) - datetime.timedelta(days=1)
    else:
        last = today.replace(month=today.month + 1, day=1) - datetime.timedelta(days=1)
    return first.isoformat(), last.isoformat()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! عدد مصرف را وارد کنید یا از دستورات استفاده کنید. برای راهنما، دستور /help را بزنید.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/help - راهنمای دستورات\n"
        "/reset_day - ریست اطلاعات امروز\n"
        "/reset_week - ریست اطلاعات این هفته\n"
        "/report - گزارش مصرف این هفته\n"
        "/month - گزارش مصرف این ماه"
    )


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


async def reset_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    week_start = datetime.date.fromisoformat(get_week_start())
    today = datetime.date.today()

    if user_id in data:
        for day in list(data[user_id].keys()):
            date_obj = datetime.date.fromisoformat(day)
            if week_start <= date_obj <= today:
                del data[user_id][day]
        save_data(data)
        await update.message.reply_text("✅ مصرف هفته پاک شد.")
    else:
        await update.message.reply_text("ℹ️ داده‌ای برای پاک کردن نبود.")


async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    week_start = datetime.date.fromisoformat(get_week_start())
    today = datetime.date.today()

    total = Decimal("0")
    if user_id in data:
        for day, value in data[user_id].items():
            date_obj = datetime.date.fromisoformat(day)
            if week_start <= date_obj <= today:
                total += Decimal(str(value))

    await update.message.reply_text(f"📊 مجموع مصرف هفته جاری: {total} عدد")


async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    first, last = get_month_range()
    d_first = datetime.date.fromisoformat(first)
    d_last = datetime.date.fromisoformat(last)

    total = Decimal("0")
    if user_id in data:
        for day, value in data[user_id].items():
            date_obj = datetime.date.fromisoformat(day)
            if d_first <= date_obj <= d_last:
                total += Decimal(str(value))

    await update.message.reply_text(f"📆 گزارش ماهانه\nاز {first} تا {last}:\n🔢 مجموع مصرف: {total} عدد")


async def add_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        num = Decimal(update.message.text.replace(",", "."))
    except InvalidOperation:
        await update.message.reply_text("❌ لطفاً یک عدد صحیح یا اعشاری وارد کنید.")
        return

    data = load_data()
    today = get_today()

    if user_id not in data:
        data[user_id] = {}
    if today not in data[user_id]:
        data[user_id][today] = 0

    data[user_id][today] = float(Decimal(str(data[user_id][today])) + num)
    save_data(data)
    await update.message.reply_text(f"✅ ثبت شد. مجموع امروز: {data[user_id][today]} عدد")


async def auto_week_reset(app: ApplicationBuilder):
    import asyncio
    while True:
        now = datetime.datetime.now()
        if now.weekday() == 5 and now.hour == 0 and now.minute == 0:
            # شنبه، 00:00
            data = load_data()
            for user_id in data:
                total = Decimal("0")
                for day, value in data[user_id].items():
                    d = datetime.date.fromisoformat(day)
                    if d >= datetime.date.today() - datetime.timedelta(days=7):
                        total += Decimal(str(value))
                await app.bot.send_message(chat_id=user_id,
                                           text=f"🗓 پایان هفته!\n🔢 مجموع مصرف هفته گذشته: {total}\nهفته جدید شروع شد.")
                # پاک‌سازی هفته گذشته
                data[user_id] = {}
            save_data(data)
        await asyncio.sleep(60)


async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("help", "نمایش راهنما"),
        BotCommand("reset_day", "ریست روزانه"),
        BotCommand("reset_week", "ریست هفته جاری"),
        BotCommand("report", "گزارش هفته جاری"),
        BotCommand("month", "گزارش ماهانه")
    ])


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset_day", reset_day))
    app.add_handler(CommandHandler("reset_week", reset_week))
    app.add_handler(CommandHandler("report", report_week))
    app.add_handler(CommandHandler("month", report_month))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_number))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )

    import asyncio
    asyncio.create_task(auto_week_reset(app))
    asyncio.run(set_commands(app))
