from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
from datetime import datetime

# تنظیمات اتصال به دیتابیس SQLite
def setup_db():
    conn = sqlite3.connect("medication_log.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (user_id INTEGER, date TEXT, amount INTEGER)''')
    conn.commit()
    return conn

# ثبت مصرف قرص
def take(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    amount = 1  # مصرف 1 قرص به صورت پیش‌فرض
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # ذخیره کردن مصرف در دیتابیس
    conn = setup_db()
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_id, date, amount) VALUES (?, ?, ?)", (user_id, current_date, amount))
    conn.commit()
    conn.close()

    update.message.reply_text(f"مصرف {amount} قرص ثبت شد.")

# گزارش مصرف روزانه
def report(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    date = context.args[0] if context.args else datetime.now().strftime('%Y-%m-%d')

    conn = setup_db()
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM logs WHERE user_id = ? AND date = ?", (user_id, date))
    result = c.fetchone()[0]
    conn.close()

    if result:
        update.message.reply_text(f"در تاریخ {date} شما {result} قرص مصرف کرده‌اید.")
    else:
        update.message.reply_text(f"هیچ مصرفی در تاریخ {date} ثبت نشده است.")

# گزارش مصرف هفتگی
def week_report(update: Update, context: CallbackContext):
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
        update.message.reply_text(f"در این هفته، از تاریخ {start_of_week} تا {end_of_week}, شما {result} قرص مصرف کرده‌اید.")
    else:
        update.message.reply_text("هیچ مصرفی برای این هفته ثبت نشده است.")

# دستور شروع
def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! من ربات ثبت مصرف قرص هستم. برای ثبت مصرف، دستور /take رو بزنید.")

def main():
    updater = Updater("7531144404:AAG047TB-zn1tCUMxZt8IPBSrZFfbDqsT0I", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("take", take))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CommandHandler("week", week_report))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
