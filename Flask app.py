from flask import Flask, render_template, request, redirect, url_for, flash
import os
import datetime
import pytz
import psycopg2
from psycopg2.extras import DictCursor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
            return_time VARCHAR(10),
            go_home BOOLEAN DEFAULT FALSE,
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
        cur.execute("SELECT status_date, status_type, time, return_time, go_home FROM work_status;")
        work_status = {"休み": [], "遅刻": {}, "早退": {}, "外出中": {}, "休憩中": []}
        for row in cur.fetchall():
            if row['status_type'] == "休み":
                work_status["休み"].append(row['holiday_date'])
            elif row['status_type'] == "遅刻":
                work_status["遅刻"][str(row['status_date'])] = row['time']
            elif row['status_type'] == "早退":
                work_status["早退"][str(row['status_date'])] = row['time']
            elif row['status_type'] == "外出中":
                work_status["外出中"][str(row['status_date'])] = {
                    "return_time": row['return_time'],
                    "go_home": row['go_home']
                }
            elif row['status_type'] == "休憩中":
                work_status["休憩中"].append(row['status_date'])
        return work_status

holidays = load_holidays()
work_status = load_work_status()

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month

    # カレンダー生成
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
        week.append((current_date.day, "勤務中", is_holiday))  # 簡易的に"勤務中"を表示
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

@app.route("/send_email", methods=["POST"])
def send_email():
    """メールを送信する"""
    subject = request.form.get("subject", "No Subject")
    body = request.form.get("body", "No Content")
    recipient = "masato_o@mac.com"
    sender = "your-email@gmail.com"
    app_password = "your-app-password"  # アプリパスワードを設定

    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, recipient, msg.as_string())
        flash("メールを送信しました", "success")
    except Exception as e:
        flash(f"メール送信中にエラーが発生しました: {e}", "error")

    return redirect(url_for("calendar"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render指定ポート
    app.run(host="0.0.0.0", port=port)  # 外部アクセスを許可
