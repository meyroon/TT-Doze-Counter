import os
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update
from datetime import datetime
import json

# توکن ربات
TOKEN = "7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I"

# آدرس وبهوک
WEBHOOK_URL = "https://tt-doze-counter.onrender.com"

# فایل ذخیره‌سازی
DATA_FILE = "data.json"


# تابع بارگذاری دیتا
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


# تابع ذخیره دیتا
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# دستور استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("به ربات شمارش دوز خوش آمدید! لطفاً عدد دوز مصرفی را ارسال کنید.")


# ثبت دوز
async def handle_dose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip().replace(",", ".")

    try:
        dose = float(text)
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد اعشاری یا صحیح ارسال کنید.")
        return

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H:%M:%S")

    data = load_data()
    data.setdefault(user_id, {}).setdefault(date_str, []).append({
        "value": dose,
        "time": timestamp
    })

    save_data(data)
    await update.message.reply_text(f"✅ دوز {dose} ثبت شد. ساعت {timestamp}")

    # نمایش مجدد گزینه‌ها
    await send_menu(update)


# گزارش روزانه
async def report_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    date_str = datetime.now().strftime("%Y-%m-%d")

    data = load_data()
    doses = data.get(user_id, {}).get(date_str, [])

    if not doses:
        await update.message.reply_text("برای امروز هنوز چیزی ثبت نشده.")
        return

    total = sum(d["value"] for d in doses)
    details = "\n".join([f"{d['time']}: {d['value']}" for d in doses])

    await update.message.reply_text(f"📅 گزارش امروز:\nمجموع: {total}\n{details}")
    await send_menu(update)


# گزارش هفتگی
async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})

    if not user_data:
        await update.message.reply_text("اطلاعاتی برای هفته جاری وجود ندارد.")
        return

    lines = []
    total = 0
    for day, entries in sorted(user_data.items()):
        subtotal = sum(e["value"] for e in entries)
        lines.append(f"{day}: {subtotal}")
        total += subtotal

    report = "\n".join(lines) + f"\n\n📊 مجموع کل: {total}"
    await update.message.reply_text(f"📆 گزارش هفتگی:\n{report}")
    await send_menu(update)


# ریست روزانه
async def reset_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    date_str = datetime.now().strftime("%Y-%m-%d")

    data = load_data()
    if user_id in data and date_str in data[user_id]:
        del data[user_id][date_str]
        save_data(data)
        await update.message.reply_text("🔁 اطلاعات امروز حذف شد.")
    else:
        await update.message.reply_text("اطلاعاتی برای امروز وجود نداشت.")
    await send_menu(update)


# منو اصلی
async def send_menu(update: Update):
    await update.message.reply_text("👇 گزینه‌ها:\n"
                                    "/day_report - گزارش امروز\n"
                                    "/week_report - گزارش هفتگی\n"
                                    "/reset_day - حذف اطلاعات امروز")


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("day_report", report_day))
    app.add_handler(CommandHandler("week_report", report_week))
    app.add_handler(CommandHandler("reset_day", reset_day))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dose))

    print("🎯 Setting webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL + f"/{TOKEN}"
    )
