from flask import Flask, render_template, request, redirect, url_for
import datetime

app = Flask(__name__)

# グローバル変数
holidays = []  # 休みの日のリスト
work_status = {"遅刻": {}, "早退": {}}  # 遅刻・早退の日と時刻

# カレンダーを生成する関数
def get_calendar(year, month):
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    calendar = []
    week = []
    current_date = first_day

    # 月曜日から始まるカレンダーのため調整
    while current_date.weekday() != 0:
        week.append(0)
        current_date -= datetime.timedelta(days=1)
    current_date = first_day

    while current_date <= last_day:
        week.append(current_date)
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

# ステータスを取得する関数
def get_day_status(day):
    day_str = str(day)

    # 休みの日
    if day in holidays:
        return "休み"

    # 遅刻の日
    if day_str in work_status["遅刻"]:
        late_time = work_status["遅刻"][day_str]
        current_time = datetime.datetime.now().time()
        if current_time < datetime.datetime.strptime(late_time, "%H:%M").time():
            return f"遅刻中 {late_time} 出勤予定"
        else:
            return "出勤中"

    # 早退の日
    if day_str in work_status["早退"]:
        early_time = work_status["早退"][day_str]
        current_time = datetime.datetime.now().time()
        if current_time < datetime.datetime.strptime(early_time, "%H:%M").time():
            return f"{early_time} 早退予定"
        else:
            return "早退済"

    # 平日かつ「休み」、「遅刻中」、「早退済み」でない場合に出勤中を表示
    if day.weekday() < 5:  # 平日かつ勤務日
        return "出勤中"

    # 上記以外は勤務外
    return "勤務外"

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month
    month_days = get_calendar(year, month)
    day_statuses = {str(day): get_day_status(day) for week in month_days for day in week if day != 0}

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        today=today.day,
        month_days=month_days,
        day_statuses=day_statuses
    )

@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status

    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        if not date:
            return redirect(url_for("manage"))

        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()

        if action == "add_holiday":
            if date_obj not in holidays:
                holidays.append(date_obj)
        elif action == "remove_holiday":
            if date_obj in holidays:
                holidays.remove(date_obj)
        elif action == "add_late":
            time = request.form.get("time")
            if time:
                work_status["遅刻"][str(date_obj)] = time
        elif action == "remove_late":
            if str(date_obj) in work_status["遅刻"]:
                del work_status["遅刻"][str(date_obj)]
        elif action == "add_early":
            time = request.form.get("time")
            if time:
                work_status["早退"][str(date_obj)] = time
        elif action == "remove_early":
            if str(date_obj) in work_status["早退"]:
                del work_status["早退"][str(date_obj)]

        return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
