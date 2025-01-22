import os
import datetime
import pytz
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask アプリケーションの初期化
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

# SMTP設定
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")  # 環境変数から取得
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # 環境変数から取得

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set.")
    raise Exception("DATABASE_URL is not set.")

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

def create_tables():
    """必要なテーブルを作成する"""
    db = get_db()
    try:
        with db.cursor() as cur:
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
                additional_info TEXT,
                UNIQUE (status_date, status_type)
            );
            """)
            db.commit()
            logger.info("Tables created or already exist")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tables: {e}")

@app.route("/")
def calendar():
    """カレンダーを表示"""
    today = datetime.date.today()
    year, month = today.year, today.month
    first_day = datetime.date(year, month, 1)
    last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1) if month < 12 else datetime.date(year, 12, 31)

    db = get_db()
    holidays = []
    work_status = []

    try:
        with db.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT holiday_date FROM holidays;")
            holidays = [row['holiday_date'] for row in cur.fetchall()]
            cur.execute("SELECT status_date, status_type, time FROM work_status;")
            work_status = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error loading calendar data: {e}")

    month_days = []
    week = []
    current_date = first_day

    # 月の最初の週の空白セルを埋める
    while current_date.weekday() != 0:
        week.append((0, "", False))
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5 or current_date in holidays
        status = next((ws['status_type'] for ws in work_status if ws['status_date'] == current_date), "")
        week.append((current_date.day, status, is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    # 最後の週の空白セルを埋める
    while len(week) < 7:
        week.append((0, "", False))
    if week:
        month_days.append(week)

    today_status = next((ws['status_type'] for ws in work_status if ws['status_date'] == today), "")

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days, today_status=today_status)

@app.route("/popup")
def popup():
    """連絡フォームのポップアップを表示"""
    day = request.args.get("day", "不明な日付")
    return render_template("popup.html", day=day)

@app.route("/send_email", methods=["POST"])
def send_email():
    """メールを送信する"""
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

        return render_template("sent.html", message="メール送信が完了しました")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return render_template("sent.html", message=f"メール送信中にエラーが発生しました: {e}")

# ログインが必要なデコレーター
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    """管理者ログインページ"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin_username = "masato"
        admin_password_hash = generate_password_hash("masato2024")

        if username == admin_username and check_password_hash(admin_password_hash, password):
            session['logged_in'] = True
            flash("ログインに成功しました")
            return redirect(url_for('manage'))
        else:
            flash("ユーザー名またはパスワードが間違っています")
    return render_template("login.html")

@app.route("/logout")
def logout():
    """ログアウト"""
    session.pop('logged_in', None)
    flash("ログアウトしました")
    return redirect(url_for('login'))

@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage():
    """管理画面"""
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        time = request.form.get("time")
        go_home = request.form.get("go_home")
        try:
            with db.cursor() as cur:
                if action == "add_holiday":
                    cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                elif action == "delete_holiday":
                    cur.execute("DELETE FROM holidays WHERE holiday_date = %s;", (date,))
                elif action == "add_late":
                    cur.execute("INSERT INTO work_status (status_date, status_type, time) VALUES (%s, '遅刻', %s) ON CONFLICT DO NOTHING;", (date, time))
                elif action == "add_early":
                    cur.execute("INSERT INTO work_status (status_date, status_type, time) VALUES (%s, '早退', %s) ON CONFLICT DO NOTHING;", (date, time))
                elif action == "add_outside":
                    status_type = "直帰予定" if go_home else "外出中"
                    cur.execute("INSERT INTO work_status (status_date, status_type) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (date, status_type))
                elif action == "add_break":
                    cur.execute("INSERT INTO work_status (status_date, status_type) VALUES (%s, '休憩中') ON CONFLICT DO NOTHING;", (date,))
                elif action == "delete_status":
                    status_type = request.form.get("status_type")
                    cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, status_type))
                db.commit()
                flash("操作が成功しました")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in manage operation: {e}")
            flash(f"エラーが発生しました: {e}")

    with db.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT * FROM holidays;")
        holidays = cur.fetchall()
        cur.execute("SELECT * FROM work_status;")
        work_status = cur.fetchall()

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    with app.app_context():
        create_tables()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
