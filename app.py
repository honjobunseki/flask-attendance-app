import os
import datetime
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, g
import psycopg2
from psycopg2.extras import DictCursor
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask アプリケーションの初期化
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

if not DATABASE_URL or not SMTP_EMAIL or not SMTP_PASSWORD:
    logger.error("必要な環境変数が設定されていません")
    raise Exception("環境変数が不足しています")


def get_db():
    """データベース接続を取得"""
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(DATABASE_URL, sslmode="require")
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    return g.db


@app.teardown_appcontext
def close_db(error):
    """アプリケーション終了時にデータベース接続を閉じる"""
    db = g.pop('db', None)
    if db is not None:
        db.close()
        logger.info("Database connection closed")


def delete_old_messages():
    """1週間以上経過した伝言を削除"""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM messages WHERE created_at < NOW() - INTERVAL '7 days';")
            db.commit()
            logger.info("1週間以上経過した伝言を削除しました")
    except Exception as e:
        db.rollback()
        logger.error(f"古い伝言の削除中にエラーが発生しました: {e}")


@app.route("/popup")
def popup():
    """ポップアップウィンドウを表示"""
    day = request.args.get("day", "不明な日付")
    status = request.args.get("status", "特になし")
    return render_template("popup.html", day=day, status=status)


@app.route("/send_email", methods=["POST"])
def send_email():
    """メールを送信して sent.html に移行"""
    subject = request.form.get("subject", "No Subject")
    body = request.form.get("body", "No Content")
    recipient = "masato_o@mac.com"

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, recipient, msg.as_string())

        logger.info("メールが送信されました")
        return render_template("sent.html", message="送信が完了しました")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return render_template("sent.html", message=f"送信中にエラーが発生しました: {e}")


@app.route("/", methods=["GET", "POST"])
def calendar():
    """カレンダーと伝言板を表示"""
    today = datetime.date.today()
    year, month = today.year, today.month
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)

    db = get_db()
    holidays = []
    work_status = []
    messages = []

    # POSTリクエストで伝言を保存
    if request.method == "POST" and "message" in request.form:
        direction = request.form.get("direction")
        message = request.form.get("message")
        try:
            with db.cursor() as cur:
                cur.execute("INSERT INTO messages (direction, message) VALUES (%s, %s);", (direction, message))
                db.commit()
                flash("伝言が保存されました")
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving message: {e}")
            flash("伝言の保存中にエラーが発生しました")

    # データを取得
    try:
        with db.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT holiday_date FROM holidays;")
            holidays = [row['holiday_date'] for row in cur.fetchall()]

            cur.execute("SELECT status_date, status_type, time FROM work_status;")
            work_status = [dict(row) for row in cur.fetchall()]

            cur.execute("""
                SELECT direction, message, created_at
                FROM messages
                ORDER BY created_at DESC;
            """)
            messages = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error loading data: {e}")

    # 最新の伝言に「NEW」を追加
    for direction in ["昌人より", "昌人へ"]:
        for message in messages:
            if message["direction"] == direction:
                message["is_new"] = True
                break

    # カレンダー生成
    month_days = []
    week = []
    current_date = first_day

    while current_date.weekday() != 0:
        week.append((0, "", False))
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5 or current_date in holidays
        status = ""
        for ws in work_status:
            if ws['status_date'] == current_date:
                if ws['status_type'] == "休み":
                    is_holiday = True
                elif ws['status_type'] == "遅刻":
                    status = f"{ws['time']} 出勤予定"
                elif ws['status_type'] == "早退":
                    status = f"{ws['time']} 早退予定"
                elif ws['status_type'] == "直帰予定":
                    status = "外出中（直帰予定）"
                elif ws['status_type'] == "外出中":
                    status = "外出中"
                elif ws['status_type'] == "休憩中":
                    status = "休憩中"
        week.append((current_date.day, status, is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    today_status = next((ws['status_type'] for ws in work_status if ws['status_date'] == today), "")

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        today=today.day,
        month_days=month_days,
        today_status=today_status,
        messages=messages,
        gif_path="/image/image_new.gif"
    )


if __name__ == "__main__":
    # アプリ起動時に古い伝言を削除
    delete_old_messages()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
