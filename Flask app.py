from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import pytz
import os
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = "your_secret_key"

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set. Please configure it in your environment.")

# データベース接続
conn = psycopg2.connect(DATABASE_URL, sslmode="require")


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
            additional_info VARCHAR(50),
            UNIQUE (status_date, status_type)
        );
        """)
        conn.commit()


create_tables()


def load_holidays():
    """休日データを取得"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT holiday_date FROM holidays;")
        return [row['holiday_date'] for row in cur.fetchall()]


def load_work_status():
    """勤務状態データを取得"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT status_date, status_type, time, additional_info FROM work_status;")
        work_status = {"休み": [], "遅刻": {}, "早退": {}, "外出中": {}, "休憩中": []}
        for row in cur.fetchall():
            if row['status_type'] == "休み":
                work_status["休み"].append(row['status_date'])
            elif row['status_type'] == "遅刻":
                work_status["遅刻"][str(row['status_date'])] = row['time']
            elif row['status_type'] == "早退":
                work_status["早退"][str(row['status_date'])] = row['time']
            elif row['status_type'] == "外出中":
                work_status["外出中"][str(row['status_date'])] = row['additional_info']
            elif row['status_type'] == "休憩中":
                work_status["休憩中"].append(row['status_date'])
        return work_status


holidays = load_holidays()
work_status = load_work_status()


def get_status(date):
    """日付のステータスを取得"""
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))
    if date in holidays:
        return "休み"
    if str(date) in work_status["遅刻"]:
        return f"遅刻予定: {work_status['遅刻'][str(date)]}"
    if str(date) in work_status["早退"]:
        return f"早退予定: {work_status['早退'][str(date)]}"
    if str(date) in work_status["外出中"]:
        return f"外出中 ({work_status['外出中'][str(date)]})"
    if date in work_status["休憩中"]:
        return "休憩中"
    if date == now.date():
        return "勤務中"
    return ""


@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    # カレンダー用の日付リスト作成
    while current_date.weekday() != 0:
        week.append((0, "", False))
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        status = get_status(current_date)
        is_holiday = current_date.weekday() >= 5 or current_date in holidays
        week.append((current_date.day, status, is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days)


@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status

    if request.method == "POST":
        date = request.form.get("date")
        action = request.form.get("action")
        time = request.form.get("time")
        go_home = request.form.get("go_home")  # "on" or None
        additional_info = "直帰予定" if go_home == "on" else None

        if action == "add_holiday":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                conn.commit()
                holidays = load_holidays()
                flash(f"{date} を休日として追加しました。")

        elif action == "add_late":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO work_status (status_date, status_type, time) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                            (date, "遅刻", time))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} に遅刻予定 {time} を追加しました。")

        elif action == "add_early":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO work_status (status_date, status_type, time) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                            (date, "早退", time))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} に早退予定 {time} を追加しました。")

        elif action == "add_outside":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO work_status (status_date, status_type, additional_info) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                            (date, "外出中", additional_info))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} に外出中を追加しました（{additional_info or '直帰なし'}）。")

        elif action == "add_break":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO work_status (status_date, status_type) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                            (date, "休憩中"))
                conn.commit()
                work_status = load_work_status()
                flash(f"{date} に休憩中を追加しました。")

    return render_template("manage.html", holidays=holidays, work_status=work_status)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
