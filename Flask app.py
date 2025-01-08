from flask import Flask, render_template, request, redirect, url_for
import datetime
import pytz

app = Flask(__name__)

# グローバル変数
holidays = []  # 祝日リスト
work_status = {"休み": [], "遅刻": {}, "早退": {}}  # 勤務ステータス

def get_today_status(date):
    """本日のステータスを取得する関数"""
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

    # デバッグログを追加
    print(f"Debug: 現在の日付 = {now.date()}, 時刻 = {now.time()}, 曜日 (0=月) = {now.weekday()}")
    print(f"Debug: 渡された日付 = {date}, 曜日 (0=月) = {date.weekday()}")

    # 日付が本日と一致しない場合は勤務外
    if date != now.date():
        return "勤務外"

    # 「休み」の場合
    if date in holidays:
        return "休み"

    # 「遅刻」の場合
    if str(date) in work_status["遅刻"]:
        late_time = datetime.datetime.strptime(work_status["遅刻"][str(date)], "%H:%M").time()
        if now.time() < late_time:
            return f"遅刻中 {late_time.strftime('%H:%M')}出勤予定"
        else:
            return "勤務中"

    # 「早退」の場合
    if str(date) in work_status["早退"]:
        early_time = datetime.datetime.strptime(work_status["早退"][str(date)], "%H:%M").time()
        if now.time() < early_time:
            return f"{early_time.strftime('%H:%M')}早退予定"
        else:
            return "早退済み"

    # 勤務時間内かどうか
    if date.weekday() < 5 and datetime.time(9, 30) <= now.time() <= datetime.time(17, 30):
        return "出勤中"

    # 上記以外
    return "勤務外"

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month

    # 月のカレンダーを生成
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    # 月曜日から始まるカレンダーに調整
    while current_date.weekday() != 0:
        week.append(0)
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        week.append(current_date.day)
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append(0)
    if week:
        month_days.append(week)

    today_status = get_today_status(today)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days, today_status=today_status, holidays=holidays, work_status=work_status)

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

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
