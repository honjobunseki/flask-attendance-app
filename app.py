import os
import datetime
import pytz
import logging
from flask import Flask, render_template, request, flash
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask アプリケーションの初期化
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

# SMTP 設定
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")  # 環境変数から取得
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # 環境変数から取得

# カレンダー表示エンドポイント
@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month

    # 月初と月末の日付
    first_day = datetime.date(year, month, 1)
    if month < 12:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    else:
        last_day = datetime.date(year, 12, 31)

    # カレンダーのデータ構築
    month_days = []
    week = []
    current_date = first_day
    while current_date.weekday() != 0:
        week.append((0, "", False))  # 空白セル
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5  # 土日を祝日扱い
        status = ""  # デフォルトのステータス
        week.append((current_date.day, status, is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    # 最後の週の空白セル埋め
    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    today_status = ""  # 本日のステータス

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days, today_status=today_status)

# ポップアップ表示エンドポイント
@app.route("/popup")
def popup():
    day = request.args.get("day", "不明な日付")
    status = request.args.get("status", "特になし")
    return render_template("popup.html", day=day, status=status)

# メール送信エンドポイント
@app.route("/send_email", methods=["POST"])
def send_email():
    try:
        subject = request.form.get("subject", "No Subject")
        body = request.form.get("body", "No Content")
        recipient = os.environ.get("EMAIL_RECIPIENT", "example@example.com")

        # メール作成
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # メール送信
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, recipient, msg.as_string())

        flash("メール送信が完了しました")
        return render_template("sent.html", message="メール送信が完了しました")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return render_template("sent.html", message=f"メール送信中にエラーが発生しました: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
