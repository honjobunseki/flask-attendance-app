from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Database setup
DB_PATH = "holidays.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS working_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                start_time TEXT,
                end_time TEXT
            )
        """)
        conn.commit()

init_db()

@app.route("/")
def calendar():
    today = datetime.today()
    current_year = today.year
    current_month = today.month

    # Get holidays from database
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date FROM holidays")
        holidays = [row[0] for row in cursor.fetchall()]

    return render_template(
        "calendar.html",
        year=current_year,
        month=current_month,
        today=today.day,
        holidays=holidays
    )

@app.route("/manage", methods=["GET", "POST"])
def manage():
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if action == "add_holiday":
                try:
                    cursor.execute("INSERT INTO holidays (date) VALUES (?)", (date,))
                    conn.commit()
                except sqlite3.IntegrityError:
                    pass  # Ignore duplicates
            elif action == "remove_holiday":
                cursor.execute("DELETE FROM holidays WHERE date = ?", (date,))
                conn.commit()
            elif action == "set_working_hours":
                cursor.execute("""
                    INSERT INTO working_hours (date, start_time, end_time)
                    VALUES (?, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET start_time=excluded.start_time, end_time=excluded.end_time
                """, (date, start_time, end_time))
                conn.commit()

    # Fetch data for display
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date FROM holidays")
        holidays = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT date, start_time, end_time FROM working_hours")
        working_hours = cursor.fetchall()

    return render_template(
        "manage.html",
        holidays=holidays,
        working_hours=working_hours
    )

if __name__ == "__main__":
    # Bind to port for Render compatibility
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
