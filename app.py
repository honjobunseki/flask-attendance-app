import os
import datetime
import logging
from flask import Flask, render_template, request, redirect, url_for, g
import psycopg2
from psycopg2.extras import DictCursor
import jpholiday

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask アプリケーションの初期化
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

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
    message_from_masato = ""
    message_to_masato = ""

    try:
        with db.cursor(cursor_factory=DictCursor) as cur:
            # 休日データを取得
            cur.execute("SELECT holiday_date FROM holidays;")
            holidays = [row['holiday_date'] for row in cur.fetchall()]

            # 勤務状態データを取得
            cur.execute("SELECT status_date, status_type, time FROM work_status;")
            work_status = [dict(row) for row in cur.fetchall()]

            # 伝言板データを取得
            cur.execute("SELECT message FROM messages WHERE direction = 'from_masato';")
            message_from_masato = cur.fetchone()['message'] if cur.rowcount > 0 else ""
            cur.execute("SELECT message FROM messages WHERE direction = 'to_masato';")
            message_to_masato = cur.fetchone()['message'] if cur.rowcount > 0 else ""
    except Exception as e:
        logger.error(f"Error loading data: {e}")

    if request.method == "POST":
        direction = request.form.get("direction")
        new_message = request.form.get("message")
        try:
            with db.cursor() as cur:
                cur.execute("""
                    INSERT INTO messages (direction, message)
                    VALUES (%s, %s)
                    ON CONFLICT (direction) DO UPDATE SET message = EXCLUDED.message;
                """, (direction, new_message))
                db.commit()
                flash("メッセージが更新されました")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating message: {e}")
            flash("メッセージ更新中にエラーが発生しました")
        return redirect(url_for('calendar'))

    month_days = []
    week = []
    current_date = first_day

    # 月の最初の週の空白セルを埋める
    while current_date.weekday() != 0:
        week.append((0, "", False))
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        # 土日または「休み」の設定がある場合は赤く塗りつぶす
        is_holiday = current_date.weekday() >= 5 or current_date in holidays or jpholiday.is_holiday(current_date)
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

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days, 
                           today_status=today_status, 
                           message_from_masato=message_from_masato, 
                           message_to_masato=message_to_masato)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
