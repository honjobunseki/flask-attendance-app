import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, time

app = Flask(__name__)

DB_PATH = "holidays.db"

# Database Initialization
def initialize_database():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS working_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                start_time TEXT,
                end_time TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized.")

# Call the initialization function
initialize_database()

# Helper functions
def get_holidays():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM holidays")
    holidays = [row[0] for row in cursor.fetchall()]
    conn.close()
    return holidays

def is_today_holiday():
    today = datetime.now().strftime("%Y-%m-%d")
    return today in get_holidays()

def get_working_hours(date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT start_time, end_time FROM working_hours WHERE date = ?", (date,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    return "09:30", "17:30"  # Default working hours

# Routes
@app.route("/")
def index():
    today = datetime.now().strftime("%Y-%m-%d")
    holidays = get_holidays()
    start_time, end_time = get_working_hours(today)
    current_time = datetime.now().time()

    # Determine the status for today
    if today in holidays:
        status = "休業日"
    elif time.fromisoformat(start_time) <= current_time <= time.fromisoformat(end_time):
        status = "出勤中"
    else:
        status = "非出勤時間"

    return render_template("calendar.html", today=today, holidays=holidays, status=status)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if action == "add_holiday":
            try:
                cursor.execute("INSERT INTO holidays (date) VALUES (?)", (date,))
            except sqlite3.IntegrityError:
                pass  # Ignore duplicate entries
        elif action == "remove_holiday":
            cursor.execute("DELETE FROM holidays WHERE date = ?", (date,))
        elif action == "set_working_hours":
            start_time = request.form.get("start_time")
            end_time = request.form.get("end_time")
            cursor.execute(
                "INSERT OR REPLACE INTO working_hours (date, start_time, end_time) VALUES (?, ?, ?)",
                (date, start_time, end_time)
            )

        conn.commit()
        conn.close()
        return redirect(url_for("manage"))

    holidays = get_holidays()
    return render_template("manage.html", holidays=holidays)

if __name__ == "__main__":
    app.run(debug=True)
