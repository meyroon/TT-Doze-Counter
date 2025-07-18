from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler
import sqlite3
import datetime
import jdatetime

# ---------- تنظیمات توکن ----------
TOKEN = "توکن_بات_تو"

# ---------- اتصال به دیتابیس ----------
conn = sqlite3.connect("pill_data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS pills (
    user_id INTEGER,
    date TEXT,
    amount INTEGER
)
""")
conn.commit()

# ---------- تبدیل تاریخ میلادی به شمسی ----------
def to_jalali(date):
    d = datetime.datetime.strptime(date, "%Y-%m-%d")
    jd = jdatetime.date.fromgregorian(date=d)
    return jd.strftime("%Y/%m/%d")

# ---------- /start ----------
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("➕ افزودن 1 عدد", callback_data="add_1")],
        [InlineKeyboardButton("📊 گزارش امروز", callback_data="report_today")],
        [InlineKeyboardButton("📆 گزارش هفتگی", callback_data="report_weekly")]
    ]
    await update.message.reply_text(
        "سلام! هر وقت قرص مصرف کردی، دکمه «افزودن 1 عدد» رو بزن.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- افزودن مصرف ----------
def add_pill(user_id, amount):
    today = datetime.date.today().isoformat()
    cursor.execute("SELECT amount FROM pills WHERE user_id=? AND date=?", (user_id, today))
    row = cursor.fetchone()
    if row:
        new_amount = row[0] + amount
        cursor.execute("UPDATE pills SET amount=? WHERE user_id=? AND date=?", (new_amount, user_id, today))
    else:
        cursor.execute("INSERT INTO pills (user_id, date, amount) VALUES (?, ?, ?)", (user_id, today, amount))
    conn.commit()

# ---------- گزارش امروز ----------
def get_today_report(user_id):
    today = datetime.date.today().isoformat()
    cursor.execute("SELECT amount FROM pills WHERE user_id=? AND date=?", (user_id, today))
    row = cursor.fetchone()
    jalali = to_jalali(today)
    if row:
        return f"📅 مصرف امروز ({jalali}): {row[0]} عدد"
    else:
        return f"📅 در تاریخ امروز ({jalali}) چیزی ثبت نشده."

# ---------- گزارش هفتگی ----------
def get_weekly_report(user_id):
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=6)
    cursor.execute("SELECT date, amount FROM pills WHERE user_id=? AND date BETWEEN ? AND ?", (user_id, week_ago.isoformat(), today.isoformat()))
    rows = cursor.fetchall()
    report = "📆 گزارش هفتگی:\n\n"
    if rows:
        for date, amount in rows:
            report += f"{to_jalali(date)}: {amount} عدد\n"
    else:
        report += "هیچ چیزی ثبت نشده."
    return report

# ---------- هندل دکمه‌ها ----------
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add_1":
        add_pill(user_id, 1)
        await query.edit_message_text("✅ یک عدد مصرف ثبت شد.")
    elif query.data == "report_today":
        report = get_today_report(user_id)
        await query.edit_message_text(report)
    elif query.data == "report_weekly":
        report = get_weekly_report(user_id)
        await query.edit_message_text(report)

# ---------- اجرای برنامه ----------
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
