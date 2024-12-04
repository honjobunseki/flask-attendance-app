from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Connect to SQLite database for holidays
DB_PATH = "holidays.db"

def get_holidays():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM holidays")
    holidays = [row[0] for row in cursor.fetchall()]
    conn.close()
    return holidays

def add_holiday(date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO holidays (date) VALUES (?)", (date,))
    conn.commit()
    conn.close()

def remove_holiday(date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM holidays WHERE date = ?", (date,))
    conn.commit()
    conn.close()

@app.route('/')
def calendar():
    today = datetime.now()
    year = today.year
    month = today.month
    first_day_of_month = datetime(year, month, 1)
    day_of_week = first_day_of_month.weekday()
    holidays = get_holidays()

    days_in_month = [datetime(year, month, day + 1).strftime("%Y-%m-%d") 
                     for day in range((datetime(year, month + 1, 1) - first_day_of_month).days)]
    return render_template('calendar.html', 
                           year=year, 
                           month=month, 
                           today=today.strftime("%Y-%m-%d"),
                           holidays=holidays, 
                           days=days_in_month, 
                           start_day=day_of_week)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if request.method == 'POST':
        date = request.form.get('date')
        action = request.form.get('action')
        if action == 'add':
            add_holiday(date)
        elif action == 'remove':
            remove_holiday(date)
        return redirect(url_for('manage'))
    holidays = get_holidays()
    return render_template('manage.html', holidays=holidays)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
