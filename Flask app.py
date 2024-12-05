from flask import Flask, render_template, request, redirect, url_for
import os
import jpholiday
from datetime import datetime, timedelta

app = Flask(__name__)

# Sample data for holidays
holidays = [
    "2024-02-11",  # 建国記念の日
    "2024-02-23",  # 天皇誕生日
]

# Route for the main calendar
@app.route("/")
def calendar():
    # Get the current date
    today = datetime.now()
    year = today.year
    month = today.month

    # Generate days of the current month
    first_day = datetime(year, month, 1)
    last_day = (first_day + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    days = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    # Prepare calendar data
    calendar_data = []
    week = []
    for day in days:
        if len(week) == 0 and day.weekday() != 6:
            week.extend([""] * (day.weekday() + 1))
        week.append({
            "date": day.strftime("%Y-%m-%d"),
            "day": day.day,
            "is_holiday": day.strftime("%Y-%m-%d") in holidays or jpholiday.is_holiday(day),
            "is_today": day.date() == today.date()
        })
        if day.weekday() == 6:
            calendar_data.append(week)
            week = []
    if week:
        calendar_data.append(week)

    return render_template("calendar.html", calendar_data=calendar_data, today=today)

# Route for the manage page
@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")

        if action == "add_holiday":
            if date not in holidays:
                holidays.append(date)
        elif action == "remove_holiday":
            if date in holidays:
                holidays.remove(date)

    return render_template("manage.html", holidays=holidays)

# Main entry point for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render will use this port
    app.run(host="0.0.0.0", port=port)
