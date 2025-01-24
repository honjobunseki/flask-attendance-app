import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps
from werkzeug.security import check_password_hash
import datetime
import calendar

# .envファイルから環境変数をロード
load_dotenv()

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask アプリケーションの初期化
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")  # 環境変数から取得

# Flaskのバージョン確認ログの追加
import flask
logger.info(f"Flask version: {flask.__version__}")

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please configure it in your environment.")
    raise Exception("DATABASE_URL is not set. Please configure it in your environment.")

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

# カレンダーページのルート
@app.route("/")
def calendar_page():
    # 今日の日付を取得
    today = datetime.datetime.now()
    year, month = today.year, today.month

    # カレンダー生成
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.itermonthdays2(year, month)  # 日付と曜日のタプル

    # データをテンプレートに渡す
    return render_template("calendar.html", today=today, year=year, month=month, month_days=month_days)

# 他のルートや関数の定義...

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)  # デバッグモードを有効に
