import os
import datetime
import pytz
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import psycopg2
from psycopg2.extras import DictCursor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from werkzeug.security import check_password_hash  # パスワードハッシュチェック用

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask アプリケーションの初期化
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")  # 環境変数から取得

# SMTP 設定
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")  # 環境変数から取得
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # 環境変数から取得

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please configure it in your Render environment.")
    raise Exception("DATABASE_URL is not set. Please configure it in your Render environment.")

def get_db():
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
    db = g.pop('db', None)
    if db is not None:
        db.close()
        logger.info("Database connection closed")

def create_tables():
    """必要なテーブルを作成する"""
    db = None
    try:
        db = get_db()
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
        if db:
            db.rollback()
        logger.error(f"Error creating tables: {e}")

@app.before_first_request
def initialize():
    """アプリケーションの初回リクエスト時にテーブルを作成"""
    create_tables()

def load_holidays():
    """休日データをロード"""
    try:
        db = get_db()
        with db.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT holiday_date FROM holidays;")
            holidays = [row['holiday_date'] for row in cur.fetchall()]
            logger.info("Holidays loaded")
            return holidays
    except Exception as e:
        logger.error(f"Error loading holidays: {e}")
        return []

def load_work_status():
    """勤務状態データをロード"""
    try:
        db = get_db()
        with db.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT status_date, status_type, time FROM work_status;")
            work_status = []
            for row in cur.fetchall():
                work_status.append({
                    'status_date': row['status_date'],
                    'status_type': row['status_type'],
                    'time': row['time']
                })
            logger.info("Work status loaded")
            return work_status
    except Exception as e:
        logger.error(f"Error loading work status: {e}")
        return []

def get_status(date, holidays, work_status):
    """指定された日付のステータスを取得"""
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

    try:
        if date > now.date():
            status = []
            if date in holidays:
                status.append("休み")
            # 未来の遅刻や早退をチェック
            for ws in work_status:
                if ws['status_date'] == date:
                    if ws['status_type'] == "遅刻":
                        status.append(f"{ws['time']} 出勤予定")
                    elif ws['status_type'] == "早退":
                        status.append(f"{ws['time']} 早退予定")
            return " / ".join(status) if status else ""
        elif date < now.date():
            if date in holidays:
                return "休み"
            # 過去の早退をチェック
            for ws in work_status:
                if ws['status_date'] == date:
                    if ws['status_type'] == "早退":
                        return f"{ws['time']} 早退済み"
            return ""
        else:
            # 今日
            if date in holidays:
                return "休み"
            for ws in work_status:
                if ws['status_date'] == date:
                    if ws['status_type'] == "遅刻":
                        late_time = datetime.datetime.strptime(ws['time'], "%H:%M").time()
                        if now.time() < late_time:
                            return f"遅刻中 {late_time.strftime('%H:%M')} 出勤予定"
                    elif ws['status_type'] == "早退":
                        early_time = datetime.datetime.strptime(ws['time'], "%H:%M").time()
                        if now.time() < early_time:
                            return f"{early_time.strftime('%H:%M')} 早退予定"
                        else:
                            return "早退済み"
            # 平日で勤務時間内かどうかをチェック
            if date.weekday() < 5 and datetime.time(9, 30) <= now.time() <= datetime.time(17, 30):
                return "勤務中"
            return "勤務外"
    except Exception as e:
        logger.error(f"Error getting status for {date}: {e}")
        return "エラー"

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month

    first_day = datetime.date(year, month, 1)
    if month < 12:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    else:
        last_day = datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    # 月の最初の週の空白セルを埋める
    while current_date.weekday() != 0:
        week.append((0, "", False))
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    holidays = load_holidays()
    work_status = load_work_status()
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5 or current_date in holidays
        status = get_status(current_date, holidays, work_status)
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

    today_status = get_status(today, holidays, work_status)

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

# 認証機能の実装

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password_hash = os.environ.get("ADMIN_PASSWORD_HASH")  # ハッシュ化されたパスワードを使用

        if not admin_password_hash:
            flash("管理者パスワードが設定されていません。")
            return redirect(url_for('login'))

        if username == admin_username and check_password_hash(admin_password_hash, password):
            session['logged_in'] = True
            flash("ログインに成功しました")
            return redirect(url_for('manage'))
        else:
            flash("ユーザー名またはパスワードが間違っています")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    flash("ログアウトしました")
    return redirect(url_for('login'))

@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage():
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        time = request.form.get("time")
        go_home = request.form.get("go_home")
        # additional_info = request.form.get("additional_info", "")  # フォームに追加情報がない場合はコメントアウト

        db = None  # 初期化
        try:
            db = get_db()
            with db.cursor() as cur:
                if action == "add_holiday":
                    cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                elif action == "add_late":
                    cur.execute("""
                        INSERT INTO work_status (status_date, status_type, time) 
                        VALUES (%s, '遅刻', %s) 
                        ON CONFLICT (status_date, status_type) DO NOTHING;
                    """, (date, time))
                elif action == "add_early":
                    cur.execute("""
                        INSERT INTO work_status (status_date, status_type, time) 
                        VALUES (%s, '早退', %s) 
                        ON CONFLICT (status_date, status_type) DO NOTHING;
                    """, (date, time))
                elif action == "add_outside":
                    status_type = "直帰予定" if go_home else "外出中"
                    cur.execute("""
                        INSERT INTO work_status (status_date, status_type) 
                        VALUES (%s, %s) 
                        ON CONFLICT (status_date, status_type) DO NOTHING;
                    """, (date, status_type))
                elif action == "add_break":
                    cur.execute("""
                        INSERT INTO work_status (status_date, status_type) 
                        VALUES (%s, '休憩中') 
                        ON CONFLICT (status_date, status_type) DO NOTHING;
                    """, (date,))
                elif action == "delete_holiday":
                    cur.execute("DELETE FROM holidays WHERE holiday_date = %s;", (date,))
                elif action == "delete_status":
                    status_type = request.form.get("status_type")
                    cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, status_type))
                else:
                    flash("不明なアクションです")
                    return redirect(url_for('manage'))
                db.commit()
                flash("操作が成功しました")
        except Exception as e:
            if db:
                try:
                    db.rollback()
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
            logger.error(f"Error in manage operation: {e}")
            flash(f"操作中にエラーが発生しました: {e}")

    # データのロード
    holidays = load_holidays()
    work_status = load_work_status()

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
