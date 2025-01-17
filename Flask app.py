from flask import Flask, render_template, request, jsonify
import datetime
import pytz
import os
import psycopg2
from psycopg2.extras import DictCursor
from google.oauth2 import service_account
from googleapiclient.discovery import build
import base64

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

    try:
        # Gmail API を使ってメールを送信する処理
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        credentials = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)
        service = build('gmail', 'v1', credentials=credentials)

        # メールを作成
        message = f"From: asbestos.kensa@gmail.com\nTo: {recipient}\nSubject: {subject}\n\n{body}"
        encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")
        send_message = {'raw': encoded_message}

        # Gmail APIを使って送信
        service.users().messages().send(userId='me', body=send_message).execute()
        return jsonify({"success": True, "message": "メールを送信しました"})
    except Exception as e:
        return jsonify({"success": False, "message": f"メール送信中にエラーが発生しました: {e}"})

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
