from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import pytz
import os
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = "your_secret_key"

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set. Please configure it in your Render environment.")

# データベース接続
conn = psycopg2.connect(DATABASE_URL, sslmode="require")

def create_tables():
    """必要なテーブルを作成または更新する"""
    with conn.cursor() as cur:
        # holidays テーブル作成
        cur.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id SERIAL PRIMARY KEY,
            holiday_date DATE NOT NULL UNIQUE
        );
        """)

        # work_status テーブル作成
        cur.execute("""
        CREATE TABLE IF NOT EXISTS work_status (
            id SERIAL PRIMARY KEY,
            status_date DATE NOT NULL,
            status_type VARCHAR(20) NOT NULL,
            time VARCHAR(10),
            return_time VARCHAR(10),
            go_home BOOLEAN DEFAULT FALSE,
            UNIQUE (status_date, status_type)
        );
        """)

        # work_status に return_time カラムがない場合追加
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'work_status' AND column_name = 'return_time'
            ) THEN
                ALTER TABLE work_status ADD COLUMN return_time VARCHAR(10);
            END IF;
        END $$;
        """)

        # work_status に go_home カラムがない場合追加
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'work_status' AND column_name = 'go_home'
            ) THEN
                ALTER TABLE work_status ADD COLUMN go_home BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
        """)

        conn.commit()

# テーブル作成
create_tables()

def load_holidays():
    """休日データをロード"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT holiday_date FROM holidays;")
        return [row['holiday_date'] for row in cur.fetchall()]

def load_work_status():
    """労働状態データをロード"""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT status_date, status_type, time, return_time, go_home FROM work_status;")
        work_status = {
            "休み": [], "遅刻": {}, "早退": {},
            "外出中": {}, "休憩中": []
        }
        for row in cur.fetchall():
            if row['status_type'] == "休み":
                work_status["休み"].append(row['status_date'])
            elif row['status_type'] == "遅刻":
                work_status["遅刻"][str(row['status_date'])] = row['time']
            elif row['status_type'] == "早退":
                work_status["早退"][str(row['status_date'])] = row['time']
            elif row['status_type'] == "外出中":
                work_status["外出中"][str(row['status_date'])] = {
                    "return_time": row['return_time'],
                    "go_home": row['go_home']
                }
            elif row['status_type'] == "休憩中":
                work_status["休憩中"].append(row['status_date'])
        return work_status

holidays = load_holidays()
work_status = load_work_status()

@app.route("/manage", methods=["GET", "POST"])
def manage():
    """労働状態の管理画面"""
    global holidays, work_status

    if request.method == "POST":
        try:
            action = request.form.get("action")
            date = request.form.get("date")
            if not date:
                flash("日付を選択してください", "error")
                return redirect(url_for("manage"))

            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

            with conn.cursor() as cur:
                if action == "add_holiday":
                    cur.execute("INSERT INTO holidays (holiday_date) VALUES (%s) ON CONFLICT DO NOTHING;", (date,))
                elif action == "remove_holiday":
                    cur.execute("DELETE FROM holidays WHERE holiday_date = %s;", (date,))
                elif action == "add_late":
                    time = request.form.get("time")
                    if time:
                        cur.execute("""
                            INSERT INTO work_status (status_date, status_type, time)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (status_date, status_type) DO UPDATE SET time = EXCLUDED.time;
                        """, (date, "遅刻", time))
                elif action == "remove_late":
                    cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "遅刻"))
                elif action == "add_early":
                    time = request.form.get("time")
                    if time:
                        cur.execute("""
                            INSERT INTO work_status (status_date, status_type, time)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (status_date, status_type) DO UPDATE SET time = EXCLUDED.time;
                        """, (date, "早退", time))
                elif action == "remove_early":
                    cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "早退"))
                elif action == "add_out":
                    return_time = request.form.get("return_time")
                    go_home = request.form.get("go_home") == "on"
                    cur.execute("""
                        INSERT INTO work_status (status_date, status_type, return_time, go_home)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (status_date, status_type) DO UPDATE SET return_time = EXCLUDED.return_time, go_home = EXCLUDED.go_home;
                    """, (date, "外出中", return_time, go_home))
                elif action == "remove_out":
                    cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "外出中"))
                elif action == "add_break":
                    cur.execute("INSERT INTO work_status (status_date, status_type) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (date, "休憩中"))
                elif action == "remove_break":
                    cur.execute("DELETE FROM work_status WHERE status_date = %s AND status_type = %s;", (date, "休憩中"))

                conn.commit()

            holidays = load_holidays()
            work_status = load_work_status()
            flash("情報を更新しました", "success")
        except Exception as e:
            conn.rollback()
            flash(f"エラーが発生しました: {e}", "error")
        finally:
            return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
