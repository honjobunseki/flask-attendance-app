from flask import Flask, render_template, request, redirect, url_for, flash
import os
import psycopg2
from psycopg2.extras import DictCursor
import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set. Please configure it in your Render environment.")

# データベース接続
conn = psycopg2.connect(DATABASE_URL, sslmode="require")

# 初期化
def create_tables():
    """必要なテーブルを作成する"""
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
            return_time TIME,
            go_home BOOLEAN DEFAULT FALSE,
            UNIQUE (status_date, status_type)
        );
        """)
        conn.commit()

create_tables()

def load_holidays():
    """休日データをロード"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT holiday_date FROM holidays;")
        return [row['holiday_date'] for row in cur.fetchall()]

def load_work_status():
    """勤務状態データをロード"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
        SELECT status_date, status_type, return_time, go_home FROM work_status;
        """)
        work_status = {"休み": [], "遅刻": {}, "早退": {}, "外出中": {}, "休憩中": {}}
        for row in cur.fetchall():
            if row['status_type'] == "休み":
                work_status["休み"].append(row['status_date'])
            elif row['status_type'] == "外出中":
                work_status["外出中"][str(row['status_date'])] = {
                    "return_time": row['return_time'],
                    "go_home": row['go_home']
                }
            elif row['status_type'] == "休憩中":
                work_status["休憩中"][str(row['status_date'])] = True
        return work_status

holidays = load_holidays()
work_status = load_work_status()

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month

    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    # 前月の日付を補完
    while current_date.weekday() != 0:
        week.insert(0, (0, "", False))
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5 or current_date in holidays
        status = get_status(current_date)
        week.append((current_date.day, status, is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    return render_template("calendar.html", year=year, month=month, month_days=month_days)

@app.route("/popup")
def popup():
    day = request.args.get("day", "不明な日付")
    status = request.args.get("status", "特になし")
    return render_template("popup.html", day=day, status=status)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    """管理画面"""
    if request.method == "POST":
        status_date = request.form.get("date")
        status_type = request.form.get("status_type")
        return_time = request.form.get("return_time")
        go_home = request.form.get("go_home") == "on"

        try:
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO work_status (status_date, status_type, return_time, go_home)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (status_date, status_type)
                DO UPDATE SET return_time = EXCLUDED.return_time, go_home = EXCLUDED.go_home;
                """, (status_date, status_type, return_time, go_home))
                conn.commit()
            flash("ステータスを更新しました", "success")
        except Exception as e:
            flash(f"エラーが発生しました: {e}", "error")
        return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status)

def get_status(date):
    """指定された日付のステータスを取得"""
    if date in holidays:
        return "休み"
    if str(date) in work_status["外出中"]:
        out = work_status["外出中"][str(date)]
        if out["go_home"]:
            return "外出中 直帰予定"
        return "外出中"
    if str(date) in work_status["休憩中"]:
        return "休憩中"
    return "勤務中"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
