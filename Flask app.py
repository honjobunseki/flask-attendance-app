from flask import Flask, render_template, request, jsonify
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Gmail API スコープ設定
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# 環境変数から認証情報を取得
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN")

# Gmail API用の認証情報を設定
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

# ホームページ
@app.route("/")
def home():
    return render_template("calendar.html")

# メール送信エンドポイント
@app.route("/send-email", methods=["POST"])
def send_email():
    try:
        # クライアントからデータを受け取る
        data = request.json
        subject = data.get("subject", "No Subject")
        body = data.get("body", "No Content")
        to = "masato_o@mac.com"

        # Gmail APIを使用してメールを送信
        service = get_gmail_service()
        message = (
            f"To: {to}\r\n"
            f"Subject: {subject}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{body}"
        )
        encoded_message = {"raw": base64.urlsafe_b64encode(message.encode()).decode()}
        service.users().messages().send(userId="me", body=encoded_message).execute()

        return jsonify({"success": f"Email sent to {to} with subject '{subject}'."})
    except HttpError as error:
        return jsonify({"error": f"An error occurred: {error}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
