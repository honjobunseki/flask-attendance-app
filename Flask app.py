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
    raise Exception("DATABASE_URL is not set. Please configure it in your Render environment.")

# データベース接続
conn = psycopg2.connect(DATABASE_URL, sslmode="require")

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
            time VARCHAR(10),
            extra_info VARCHAR(50),
            UNIQUE (status_date, status_type)
        );
        """)
        conn.commit()

# テーブル作成
create_tables()

def load_holidays():
    """休日データをロード"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT holiday_date FROM holidays;")
        return [row['holiday_date'] for row in cur.fetchall()]

def load_work_status():
    """勤務状態データをロード"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT status_date, status_type, time, extra_info FROM work_status;")
        work_status = {
            "休み": [],
            "遅刻": {},
            "早退": {},
            "外出中": {},
            "休憩中": {}
        }
        for row in cur.fetchall():
            if row['status_type'] == "休み":
                work_status["休み"].append(row['status_date'])
            elif row['status_type'] in ["遅刻", "早退", "外出中", "休憩中"]:
                work_status[row['status_type']][str(row['status_date'])] = {
                    "time": row['time'],
                    "extra_info": row['extra_info']
                }
        return work_status

@app.route("/")
def calendar():
    """カレンダー画面"""
    holidays = load_holidays()
    work_status = load_work_status()

    today = datetime.date.today()
    year, month = today.year, today.month

    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    while current_date.weekday() != 0:
        week.append((0, "", False))
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5 or current_date in holidays
        status = get_status(current_date, holidays, work_status)
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

def get_status(date, holidays, work_status):
    """日付のステータスを取得"""
    status_parts = []
    if date in holidays:
        status_parts.append("休み")
    for status_type in ["遅刻", "早退", "外出中", "休憩中"]:
        if str(date) in work_status[status_type]:
            time_info = work_status[status_type][str(date)]["time"]
            extra_info = work_status[status_type][str(date)]["extra_info"]
            status = status_type
            if time_info:
                status += f" {time_info}"
            if extra_info:
                status += f" ({extra_info})"
            status_parts.append(status)
    return " / ".join(status_parts)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    """管理画面"""
    if request.method == "POST":
        date = request.form.get("date")
        status_type = request.form.get("status_type")
        time = request.form.get("time", None)
        extra_info = None
        if status_type == "外出中" and request.form.get("direct_return") == "on":
            extra_info = "直帰予定"

        try:
            if status_type == "休み":
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                    conn.commit()
                flash("休日を追加しました", "success")
            else:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO work_status (status_date, status_type, time, extra_info)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (status_date, status_type)
                        DO UPDATE SET time = EXCLUDED.time, extra_info = EXCLUDED.extra_info;
                    """, (date, status_type, time, extra_info))
                    conn.commit()
                flash(f"{status_type}を追加しました", "success")
        except Exception as e:
            conn.rollback()
            flash(f"エラー: {e}", "danger")

    holidays = load_holidays()
    work_status = load_work_status()

    return render_template("manage.html", holidays=holidays, work_status=work_status)

@app.route("/delete_status", methods=["POST"])
def delete_status():
    """ステータスを削除"""
    date = request.form.get("date")
    status_type = request.form.get("status_type")

    try:
        if status_type == "休み":
            with conn.cursor() as cur:
                cur.execute("DELETE FROM holidays WHERE holiday_date = %s;", (date,))
                conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, status_type))
                conn.commit()
        flash(f"{status_type}を削除しました", "success")
    except Exception as e:
        conn.rollback()
        flash(f"エラー: {e}", "danger")
    return redirect(url_for("manage"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
