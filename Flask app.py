from flask import Flask, render_template, request, jsonify
import os
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Gmail APIの設定
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

def send_email(subject, body):
    """Gmail APIを使用してメールを送信"""
    creds = Credentials.from_authorized_user_info({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "token_uri": "https://oauth2.googleapis.com/token"
    })

    try:
        # Gmail APIのサービスを構築
        service = build('gmail', 'v1', credentials=creds)

        # メールの作成
        message = f"From: me\nTo: masato_o@mac.com\nSubject: {subject}\n\n{body}"
        encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")
        create_message = {'raw': encoded_message}

        # メールを送信
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return send_message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

@app.route("/send-email", methods=["POST"])
def send_email_route():
    """ポップアップウィンドウからのメール送信リクエストを処理"""
    data = request.json
    subject = data.get("subject")
    body = data.get("body")

    if not subject or not body:
        return jsonify({"error": "件名と本文は必須です"}), 400

    # メール送信
    result = send_email(subject, body)
    if result:
        return jsonify({"success": "メールが送信されました"})
    else:
        return jsonify({"error": "メール送信に失敗しました"}), 500

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

    while current_date.weekday() != 0:
        week.append((0, "", False))  # 空白セル
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        week.append((current_date.day, "", False))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days)
