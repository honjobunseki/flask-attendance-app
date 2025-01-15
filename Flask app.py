from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Gmail APIの設定
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")

def send_email_via_gmail(subject, body):
    """Gmail APIを使ってメールを送信する"""
    credentials = Credentials.from_service_account_info(
        json.loads(CREDENTIALS), scopes=SCOPES)
    service = build('gmail', 'v1', credentials=credentials)
    message = {
        'raw': base64.urlsafe_b64encode(
            f"To: masato_o@mac.com\nSubject: {subject}\n\n{body}".encode("utf-8")
        ).decode("utf-8")
    }
    service.users().messages().send(userId="me", body=message).execute()

@app.route("/contact", methods=["GET"])
def contact():
    """連絡フォームの表示"""
    date = request.args.get("date", "")
    status = request.args.get("status", "")
    return render_template("contact.html", date=date, status=status)

@app.route("/send_email", methods=["POST"])
def send_email():
    """フォームから受け取ったデータをGmail APIで送信"""
    subject = request.form.get("subject")
    body = request.form.get("body")
    try:
        send_email_via_gmail(subject, body)
        flash("メールが送信されました", "success")
    except Exception as e:
        flash(f"メール送信中にエラーが発生しました: {e}", "error")
    return redirect(url_for("calendar"))
