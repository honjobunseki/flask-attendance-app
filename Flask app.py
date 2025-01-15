from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import pytz
import os
import psycopg2
from psycopg2.extras import DictCursor
from threading import Thread

app = Flask(__name__)
app.secret_key = "your_secret_key"

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set. Please configure it in your Render environment.")

# グローバル変数
conn = None
holidays = []
work_status = {"休み": [], "遅刻": {}, "早退": {}}

def connect_to_database():
    """データベースに接続"""
    global conn
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        print("Database connected successfully.")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

def create_tables():
    """必要なテーブルを作成"""
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id SERIAL PRIMARY KEY,
            holiday_date DATE NOT NULL UNIQUE
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS work_status (
            id SERIAL PRIMARY KEY,
            status_date DATE NOT NULL,
            status_type VARCHAR(20) NOT NULL,
            time VARCHAR(10),
            UNIQUE (status_date, status_type)
        );
        """)
        conn.commit()
        print("Tables created or already exist.")

def load_holidays():
    """休日データをロード"""
    global holidays
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT holiday_date FROM holidays;")
        holidays = [row['holiday_date'] for row in cur.fetchall()]
        print(f"Holidays loaded: {holidays}")

def load_work_status():
    """勤務状態データをロード"""
    global work_status
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT status_date, status_type, time FROM work_status;")
        work_status = {"休み": [], "遅刻": {}, "早退": {}}
        for row in cur.fetchall():
            if row['status_type'] == "休み":
                work_status["休み"].append(row['status_date'])
            elif row['status_type'] == "遅刻":
                work_status["遅刻"][str(row['status_date'])] = row['time']
            elif row['status_type'] == "早退":
                work_status["早退"][str(row['status_date'])] = row['time']
        print(f"Work status loaded: {work_status}")

def initialize_app():
    """アプリケーションの初期化をバックグラウンドで実行"""
    try:
        connect_to_database()
        create_tables()
        load_holidays()
        load_work_status()
        print("Application initialized successfully.")
    except Exception as e:
        print(f"Initialization error: {e}")

# バックグラウンド初期化スレッド
Thread(target=initialize_app).start()

def get_status(date):
    """指定された日付のステータスを取得"""
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

    if date > now.date():
        status = []
        if date in holidays:
            status.append("休み")
        if str(date) in work_status["遅刻"]:
            status.append(f"{work_status['遅刻'][str(date)]} 出勤予定")
        if str(date) in work_status["早退"]:
            status.append(f"{work_status['早退'][str(date)]} 早退予定")
        return " / ".join(status) if status else ""

    elif date < now.date():
        if date in holidays:
            return "休み"
        if str(date) in work_status["早退"]:
            return f"{work_status['早退'][str(date)]} 早退済み"
        return ""

    else:
        if date in holidays:
            return "休み"
        if str(date) in work_status["遅刻"]:
            late_time = datetime.datetime.strptime(work_status["遅刻"][str(date)], "%H:%M").time()
            if now.time() < late_time:
                return f"遅刻中 {late_time.strftime('%H:%M')} 出勤予定"
        if str(date) in work_status["早退"]:
            early_time = datetime.datetime.strptime(work_status["早退"][str(date)], "%H:%M").time()
            if now.time() < early_time:
                return f"{early_time.strftime('%H:%M')} 早退予定"
            else:
                return "早退済み"
        if date.weekday() < 5 and datetime.time(9, 30) <= now.time() <= datetime.time(17, 30):
            return "勤務中"
        return "勤務外"

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month

    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    while current_date.weekday() != 0:
        week.append((0, "", False))  # (日付, ステータス, 休日フラグ)
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5 or current_date in holidays
        week.append((current_date.day, get_status(current_date), is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
