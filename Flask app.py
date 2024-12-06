from flask import Flask, render_template, request, redirect, url_for
import datetime
import jpholiday

app = Flask(__name__)

# グローバル変数
holidays = []  # 祝日リスト
work_status = {"休み": [], "遅刻": {}, "早退": {}}  # 勤務ステータス

# カレンダーを生成する関数
def get_calendar(year, month):
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    calendar = []
    week = []
    current_date = first_day

    # 月曜日から始まるカレンダーのため調整
    while current_date.weekday() != 0:  # 月曜まで空白セル
        week.append(0)
        current_date -= datetime.timedelta(days=1)
    current_date = first_day

    while current_date <= last_day:
        week.append(current_date.day)
        if len(week) == 7:
            calendar.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    # 最後の週の調整
    while len(week) < 7:
        week.append(0)
    if week:
        calendar.append(week)

    return calendar

# カレンダー表示ルート
@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month
    month_days = get_calendar(year, month)

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        today=today.day,
        month_days=month_days,
        holidays=holidays,
        work_status=work_status
    )

# 管理ページルート
@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status
    data = {}  # 各日付のステータス情報を格納

    # 祝日・遅刻・早退情報をデータ化
    for date in holidays:
        data[str(date)] = {"status": "休み", "time": None}
    for date, time in work_status["遅刻"].items():
        data[date] = {"status": "遅刻", "time": time}
    for date, time in work_status["早退"].items():
        data[date] = {"status": "早退", "time": time}

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
        elif action == "add_late":
            time = request.form.get("time")
            if time:
                work_status["遅刻"][str(date)] = time
        elif action == "remove_late":
            if str(date) in work_status["遅刻"]:
                del work_status["遅刻"][str(date)]
        elif action == "add_early":
            time = request.form.get("time")
            if time:
                work_status["早退"][str(date)] = time
        elif action == "remove_early":
            if str(date) in work_status["早退"]:
                del work_status["早退"][str(date)]

        return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status, data=data)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
