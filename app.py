import os
import datetime
import pytz
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps
from werkzeug.security import check_password_hash

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask アプリケーションの初期化
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

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
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password_hash = os.environ.get("ADMIN_PASSWORD_HASH")

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
