from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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
        cur.execute("SELECT status_date, status_type, time FROM work_status;")
        work_status = {"休み": [], "遅刻": {}, "早退": {}}
        for row in cur.fetchall():
            if row['status_type'] == "休み":
                work_status["休み"].append(row['status_date'])
            elif row['status_type'] == "遅刻":
                work_status["遅刻"][str(row['status_date'])] = row['time']
            elif row['status_type'] == "早退":
                work_status["早退"][str(row['status_date'])] = row['time']
        return work_status


holidays = load_holidays()
work_status = load_work_status()


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

    today_status = get_status(today)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days, today_status=today_status)


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
                return f"{late_time.strftime('%H:%M')} 遅刻予定"
        if str(date) in work_status["早退"]:
            early_time = datetime.datetime.strptime(work_status["早退"][str(date)], "%H:%M").time()
            if now.time() < early_time:
                return f"{early_time.strftime('%H:%M')} 早退予定"
            else:
                return "早退済み"
        if date.weekday() < 5 and datetime.time(9, 0) <= now.time() <= datetime.time(18, 0):
            return "勤務中"
        return "勤務外"


@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status

    if request.method == "POST":
        try:
            action = request.form.get("action")
            date = request.form.get("date")
            if not date:
                flash("日付を選択してください", "error")
                return redirect(url_for("manage"))

            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

            with conn.cursor() as cur:
                if action == "add_holiday":
                    cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                elif action == "remove_holiday":
                    cur.execute("DELETE FROM holidays WHERE holiday_date = %s;", (date,))
                elif action == "add_late":
                    time = request.form.get("time")
                    if time:
                        cur.execute("""
                            INSERT INTO work_status (status_date, status_type, time)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (status_date, status_type) DO UPDATE SET time = EXCLUDED.time;
                        """, (date, "遅刻", time))
                elif action == "remove_late":
                    cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "遅刻"))
                elif action == "add_early":
                    time = request.form.get("time")
                    if time:
                        cur.execute("""
                            INSERT INTO work_status (status_date, status_type, time)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (status_date, status_type) DO UPDATE SET time = EXCLUDED.time;
                        """, (date, "早退", time))
                elif action == "remove_early":
                    cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "早退"))

                conn.commit()

            holidays = load_holidays()
            work_status = load_work_status()
            flash("情報を更新しました", "success")
        except Exception as e:
            conn.rollback()
            flash(f"エラーが発生しました: {e}", "error")

        return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status)


@app.route("/send_email", methods=["POST"])
def send_email():
    data = request.get_json()
    subject = data.get("subject", "")
    body = data.get("body", "")

    # Gmail API連携処理
    try:
        # Gmail API処理をここに追加
        return jsonify({"message": "メールを送信しました"})
    except Exception as e:
        return jsonify({"message": f"メールの送信に失敗しました: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
