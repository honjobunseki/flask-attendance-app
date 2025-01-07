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
    while current_date.weekday() != 0:
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

# 各日付のステータスを取得する関数
def get_status_for_date(date):
    now = datetime.datetime.now()
    date_str = date.strftime("%Y-%m-%d")

    # 「休み」の場合
    if date in holidays:
        return "休み"

    # 「遅刻」の場合
    if date_str in work_status["遅刻"]:
        late_time = datetime.datetime.strptime(work_status["遅刻"][date_str], "%H:%M").time()
        if now.time() < late_time:
            return f"遅刻中 {late_time.strftime('%H:%M')} 出勤予定"
        else:
            return "出勤中"

    # 「早退」の場合
    if date_str in work_status["早退"]:
        early_time = datetime.datetime.strptime(work_status["早退"][date_str], "%H:%M").time()
        if now.time() < early_time:
            return f"{early_time.strftime('%H:%M')} 早退予定"
        else:
            return "早退済み"

    # 出勤中の時間帯
    if date.weekday() < 5 and datetime.time(9, 30) <= now.time() <= datetime.time(17, 30):
        return "出勤中"

    # 上記以外
    return "勤務外"

# カレンダー表示ルート
@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month
    month_days = get_calendar(year, month)

    # 各日付のステータスを生成
    day_status = {}
    for week in month_days:
        for day in week:
            if day > 0:  # 空白セル（0）はスキップ
                date = datetime.date(year, month, day)
                day_status[day] = get_status_for_date(date)

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        today=today.day,
        month_days=month_days,
        day_status=day_status
    )

# 管理ページルート
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
        elif action == "add_late":
            time = request.form.get("time")
            if time:
                work_status["遅刻"][date.strftime("%Y-%m-%d")] = time
        elif action == "remove_late":
            if date.strftime("%Y-%m-%d") in work_status["遅刻"]:
                del work_status["遅刻"][date.strftime("%Y-%m-%d")]
        elif action == "add_early":
            time = request.form.get("time")
            if time:
                work_status["早退"][date.strftime("%Y-%m-%d")] = time
        elif action == "remove_early":
            if date.strftime("%Y-%m-%d") in work_status["早退"]:
                del work_status["早退"][date.strftime("%Y-%m-%d")]

        return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
