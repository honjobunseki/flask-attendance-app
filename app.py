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
        status = ""
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

    today_status = ""

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days, today_status=today_status)

if __name__ == "__main__":
    # アプリケーションコンテキスト内でテーブル作成処理を実行
    with app.app_context():
        create_tables()
    # Flaskアプリケーションを起動
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
