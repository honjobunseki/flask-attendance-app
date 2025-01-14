from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import datetime
import pytz
import os
import psycopg2
from psycopg2.extras import DictCursor
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = "your_secret_key"

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set. Please configure it in your Render environment.")

# Gmail API の設定
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")

if not GOOGLE_CREDENTIALS:
    raise Exception("GOOGLE_CREDENTIALS is not set. Please configure it in your Render environment.")

credentials = service_account.Credentials.from_service_account_info(
    eval(GOOGLE_CREDENTIALS),
    scopes=SCOPES
)
service = build('gmail', 'v1', credentials=credentials)

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

def send_email(recipient, subject, body):
    """Gmail API を使用してメールを送信"""
    message = {
        'raw': base64.urlsafe_b64encode(f"To: {recipient}\nSubject: {subject}\n\n{body}".encode()).decode()
    }
    try:
        service.users().messages().send(userId="me", body=message).execute()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route("/send_email", methods=["POST"])
def send_email_route():
    """AJAX 経由でのメール送信処理"""
    data = request.json
    recipient = "masato_o@mac.com"
    subject = data.get("subject", "連絡事項")
    body = data.get("body", "詳細を記入してください。")
    success = send_email(recipient, subject, body)
    if success:
        return jsonify({"message": "メールを送信しました。"}), 200
    else:
        return jsonify({"message": "メールの送信に失敗しました。"}), 500

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
        is_holiday = current_date.weekday() >= 5
        week.append((current_date.day, f"ステータス-{current_date.day}", is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    return render_template("calendar.html", year=year, month=month, month_days=month_days)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
