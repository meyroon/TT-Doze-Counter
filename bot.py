from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
from datetime import datetime, timedelta

# تنظیمات اتصال به دیتابیس SQLite
def setup_db():
    conn = sqlite3.connect("medication_log.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (user_id INTEGER, date TEXT, amount INTEGER)''')
    conn.commit()
    return conn

# ثبت مصرف قرص
async def take(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    amount = 1  # مصرف 1 قرص به صورت پیش‌فرض
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # ذخیره کردن مصرف در دیتابیس
    conn = setup_db()
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_id, date, amount) VALUES (?, ?, ?)", (user_id, current_date, amount))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"مصرف {amount} قرص ثبت شد.")

# گزارش مصرف روزانه
async def report(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    date = context.args[0] if context.args else datetime.now().strftime('%Y-%m-%d')

    conn = setup_db()
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM logs WHERE user_id = ? AND date = ?", (user_id, date))
    result = c.fetchone()[0]
    conn.close()

    if result:
        await update.message.reply_text(f"در تاریخ {date} شما {result} قرص مصرف کرده‌اید.")
    else:
        await update.message.reply_text(f"هیچ مصرفی در تاریخ {date} ثبت نشده است.")

# گزارش مصرف هفتگی
async def week_report(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    current_date = datetime.now()
    start_of_week = (current_date - timedelta(days=current_date.weekday())).strftime('%Y-%m-%d')
    end_of_week = (current_date + timedelta(days=(6 - current_date.weekday()))).strftime('%Y-%m-%d')

    conn = setup_db()
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM logs WHERE user_id = ? AND date BETWEEN ? AND ?", (user_id, start_of_week, end_of_week))
    result = c.fetchone()[0]
    conn.close()

    if result:
        await update.message.reply_text(f"در این هفته، از تاریخ {start_of_week} تا {end_of_week}, شما {result} قرص مصرف کرده‌اید.")
    else:
        await update.message.reply_text("هیچ مصرفی برای این هفته ثبت نشده است.")

# دستور شروع
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("سلام! من ربات ثبت مصرف قرص هستم. برای ثبت مصرف، دستور /take رو بزنید.")

def main():
    application = Application.builder().token("7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("take", take))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("week", week_report))

    application.run_polling()

if __name__ == '__main__':
    main()
