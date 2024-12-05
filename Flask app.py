from flask import Flask, render_template, request, redirect, url_for
import datetime
import jpholiday

app = Flask(__name__)

# グローバル変数
holidays = []
work_status = {"休み": [], "遅刻": {}, "早退": {}}

# カレンダーを生成する関数
def get_calendar(year, month):
    first_day = datetime.date(year, month, 1)
    last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1) if month < 12 else datetime.date(year, 12, 31)
    calendar = []
    week = []
    current_date = first_day

    while current_date.weekday() != 0:
        week.append(0)  # 空白セル
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        week.append(current_date.day)
        if len(week) == 7:
            calendar.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append(0)
    if week:
        calendar.append(week)

    return calendar

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month
    month_days = get_calendar(year, month)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days, holidays=holidays, work_status=work_status)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        if not date:
            return redirect(url_for("manage"))

        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

        if action == "add_holiday":
            if date not in holidays:
                holidays.append(date)
        elif action == "remove_holiday":
            if date in holidays:
                holidays.remove(date)
        elif action == "set_late":
            late_time = request.form.get("late_time")
            if late_time:
                work_status["遅刻"][str(date)] = late_time
        elif action == "set_early":
            early_time = request.form.get("early_time")
            if early_time:
                work_status["早退"][str(date)] = early_time

        return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
