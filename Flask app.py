from flask import Flask, render_template, request, redirect, url_for
import datetime
import pytz
import json

app = Flask(__name__)

# 永続化用のファイルパス
DATA_FILE = "data.json"

# 初期データ
holidays = []  # 祝日リスト
work_status = {"休み": [], "遅刻": {}, "早退": {}}  # 勤務ステータス

# データをJSONファイルに保存
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"holidays": holidays, "work_status": work_status}, f, ensure_ascii=False, indent=4)

# JSONファイルからデータを読み込み
def load_data():
    global holidays, work_status
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            holidays = data.get("holidays", [])
            work_status = data.get("work_status", {"休み": [], "遅刻": {}, "早退": {}})
    except FileNotFoundError:
        # ファイルがない場合はデフォルト値のまま
        pass

# 本日のステータスを取得する関数
def get_today_status(date):
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

    if date != now.date():
        return "勤務外"

    if date in holidays:
        return "休み"
    if str(date) in work_status["遅刻"]:
        late_time = datetime.datetime.strptime(work_status["遅刻"][str(date)], "%H:%M").time()
        if now.time() < late_time:
            return f"遅刻中 {late_time.strftime('%H:%M')}出勤予定"
        return "勤務中"
    if str(date) in work_status["早退"]:
        early_time = datetime.datetime.strptime(work_status["早退"][str(date)], "%H:%M").time()
        if now.time() < early_time:
            return f"{early_time.strftime('%H:%M')}早退予定"
        return "早退済み"
    if date.weekday() < 5 and datetime.time(9, 30) <= now.time() <= datetime.time(17, 30):
        return "出勤中"
    return "勤務外"

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days, week = [], []
    current_date = first_day

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

        save_data()  # データを保存
        return redirect(url_for("manage"))

    return render_template("manage.html", holidays=holidays, work_status=work_status)

if __name__ == "__main__":
    load_data()  # アプリケーション起動時にデータを読み込み
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
