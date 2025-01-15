from flask import Flask, render_template, request, jsonify
import datetime
import pytz
import os
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Gmail API スコープ設定
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Gmail API 認証情報（環境変数から取得）
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN")

# Gmail API 用の認証情報を取得
def get_gmail_service():
    credentials = Credentials.from_authorized_user_info(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": GOOGLE_REFRESH_TOKEN,
        },
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=credentials)

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

    # 前月の日付分の空白を埋める
    while current_date.weekday() != 0:
        week.insert(0, (0, "", False))  # 空白セル
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5  # 土日判定
        week.append((current_date.day, "", is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    # 月末後の空白を埋める
    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days)

@app.route("/send-email", methods=["POST"])
def send_email():
    try:
        data = request.json
        subject = data.get("subject", "No Subject")
        body = data.get("body", "No Content")
        to = "masato_o@mac.com"

        # Gmail APIでメール送信
        service = get_gmail_service()
        message = (
            f"To: {to}\r\n"
            f"Subject: {subject}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{body}"
        )
        encoded_message = {"raw": base64.urlsafe_b64encode(message.encode()).decode()}
        service.users().messages().send(userId="me", body=encoded_message).execute()

        return jsonify({"success": "メールが送信されました。"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
