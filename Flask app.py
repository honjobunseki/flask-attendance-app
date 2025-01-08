from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import pytz
import psycopg2
from psycopg2.extras import DictCursor
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# PostgreSQL接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")  # Renderの環境変数を使用
conn = psycopg2.connect(DATABASE_URL, sslmode="require")

# テーブル作成（初回実行時のみ）
def create_tables():
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id SERIAL PRIMARY KEY,
            date DATE UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS work_status (
            id SERIAL PRIMARY KEY,
            date DATE UNIQUE NOT NULL,
            status_type VARCHAR(10) NOT NULL,
            time TIME
        );
        """)
        conn.commit()

create_tables()

def get_today_status(date):
    """本日のステータスを取得する関数"""
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

    # データベースから情報を取得
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT * FROM holidays WHERE date = %s", (date,))
        holiday = cur.fetchone()

        if holiday:
            return "休み"

        cur.execute("SELECT * FROM work_status WHERE date = %s", (date,))
        status = cur.fetchone()

        if status:
            if status["status_type"] == "遅刻":
                late_time = status["time"]
                if now.time() < late_time:
                    return f"遅刻中 {late_time.strftime('%H:%M')}出勤予定"
                else:
                    return "勤務中"
            elif status["status_type"] == "早退":
                early_time = status["time"]
                if now.time() < early_time:
                    return f"{early_time.strftime('%H:%M')}早退予定"
                else:
                    return "早退済み"

    # 勤務時間内かどうか
    if date.weekday() < 5 and datetime.time(9, 30) <= now.time() <= datetime.time(17, 30):
        return "勤務中"

    # 上記以外
    return "勤務外"

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month

    # 月のカレンダーを生成
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    while current_date.weekday() != 0:
        week.append(0)
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        week.append(current_date.day)
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append(0)
    if week:
        month_days.append(week)

    today_status = get_today_status(today)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days, today_status=today_status)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        if not date:
            flash("日付を選択してください", "error")
            return redirect(url_for("manage"))

        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

        try:
            with conn.cursor() as cur:
                if action == "add_holiday":
                    cur.execute("INSERT INTO holidays (date) VALUES (%s) ON CONFLICT (date) DO NOTHING", (date,))
                elif action == "remove_holiday":
                    cur.execute("DELETE FROM holidays WHERE date = %s", (date,))
                elif action == "add_late":
                    time = request.form.get("time")
                    if time:
                        cur.execute("""
                        INSERT INTO work_status (date, status_type, time)
                        VALUES (%s, '遅刻', %s)
                        ON CONFLICT (date) DO UPDATE SET status_type = '遅刻', time = %s
                        """, (date, time, time))
                elif action == "remove_late":
                    cur.execute("DELETE FROM work_status WHERE date = %s AND status_type = '遅刻'", (date,))
                elif action == "add_early":
                    time = request.form.get("time")
                    if time:
                        cur.execute("""
                        INSERT INTO work_status (date, status_type, time)
                        VALUES (%s, '早退', %s)
                        ON CONFLICT (date) DO UPDATE SET status_type = '早退', time = %s
                        """, (date, time, time))
                elif action == "remove_early":
                    cur.execute("DELETE FROM work_status WHERE date = %s AND status_type = '早退'", (date,))
                conn.commit()
                flash("情報を更新しました", "success")
        except Exception as e:
            flash(f"エラーが発生しました: {e}", "error")
            conn.rollback()

        return redirect(url_for("manage"))

    # データの取得
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT * FROM holidays")
        holidays = cur.fetchall()
        cur.execute("SELECT * FROM work_status")
        work_status = cur.fetchall()

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
