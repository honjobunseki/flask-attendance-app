from flask import Flask, render_template, request, redirect, flash, url_for
import psycopg2
from psycopg2.extras import DictCursor
import os
import datetime
import pytz

app = Flask(__name__)
app.secret_key = "your_secret_key"

# データベース設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set. Please configure it in your environment.")

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
            additional_info VARCHAR(50),
            UNIQUE (status_date, status_type)
        );
        """)
        conn.commit()


# テーブル作成
create_tables()


def load_holidays():
    """休日データをロード"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT holiday_date FROM holidays ORDER BY holiday_date;")
        return [row["holiday_date"] for row in cur.fetchall()]


def load_work_status():
    """勤務状態データをロード"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT status_date, status_type, time, additional_info FROM work_status ORDER BY status_date;")
        return cur.fetchall()


def get_status(date, holidays, work_status):
    """指定された日付のステータスを取得"""
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

    if date in holidays:
        return "休み"
    for status in work_status:
        if status["status_date"] == date:
            if status["status_type"] == "遅刻":
                return f"遅刻 ({status['time']})"
            elif status["status_type"] == "早退":
                return f"早退 ({status['time']})"
            elif status["status_type"] == "外出中":
                additional = f"（{status['additional_info']}）" if status["additional_info"] else ""
                return f"外出中{additional}"
            elif status["status_type"] == "休憩中":
                return "休憩中"
    if date == now.date():
        return "勤務中"
    return ""


@app.route("/")
def calendar():
    """カレンダー表示"""
    today = datetime.date.today()
    year, month = today.year, today.month

    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    holidays = load_holidays()
    work_status = load_work_status()

    # 前月の余白を埋める
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


@app.route("/manage", methods=["GET", "POST"])
def manage():
    """管理画面"""
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        time = request.form.get("time")
        additional_info = None

        if action == "add_holiday" and date:
            try:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                    conn.commit()
                flash(f"休日 {date} を追加しました。")
            except Exception as e:
                flash(f"エラー: {e}")

        elif action in ["add_late", "add_early"] and date and time:
            status_type = "遅刻" if action == "add_late" else "早退"
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO work_status (status_date, status_type, time) 
                        VALUES (%s, %s, %s) ON CONFLICT (status_date, status_type) DO UPDATE SET time = EXCLUDED.time;
                    """, (date, status_type, time))
                    conn.commit()
                flash(f"{date} の {status_type} を {time} に設定しました。")
            except Exception as e:
                flash(f"エラー: {e}")

        elif action in ["add_outside", "add_break"] and date:
            status_type = "外出中" if action == "add_outside" else "休憩中"
            if action == "add_outside":
                additional_info = "直帰予定" if request.form.get("go_home") == "on" else None
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO work_status (status_date, status_type, time, additional_info) 
                        VALUES (%s, %s, NULL, %s) 
                        ON CONFLICT (status_date, status_type) DO UPDATE SET additional_info = EXCLUDED.additional_info;
                    """, (date, status_type, additional_info))
                    conn.commit()
                flash(f"{date} の {status_type} を設定しました。")
            except Exception as e:
                flash(f"エラー: {e}")

        return redirect(url_for("manage"))

    holidays = load_holidays()
    work_status = load_work_status()
    return render_template("manage.html", holidays=holidays, work_status=work_status)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
