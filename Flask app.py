from flask import Flask, render_template, request, redirect, url_for
import datetime

app = Flask(__name__)

# グローバル変数
holidays = []  # 休みの日付リスト
work_status = {"休み": [], "遅刻": {}, "早退": {}}  # 遅刻・早退情報

# カレンダーを生成する関数
def get_calendar(year, month):
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    calendar = []
    week = []
    current_date = first_day

    # 空白セルを追加（月曜始まり）
    while current_date.weekday() != 0:
        week.insert(0, 0)  # 空白セル
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        week.append(current_date.day)
        if len(week) == 7:
            calendar.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    # 最後の週を埋める
    while len(week) < 7:
        week.append(0)
    if week:
        calendar.append(week)

    return calendar

# 今日のステータスを取得
def get_today_status(today):
    now = datetime.datetime.now()
    date_str = str(today)

    # 平日で勤務時間内かどうか
    is_weekday = today.weekday() < 5  # 月曜～金曜
    is_working_hours = datetime.time(9, 30) <= now.time() <= datetime.time(17, 30)

    # 「休み」の場合
    if today in holidays:
        return "休み"

    # 「遅刻」の場合
    if date_str in work_status["遅刻"]:
        late_time = datetime.datetime.strptime(work_status["遅刻"][date_str], "%H:%M").time()
        if now.time() < late_time:  # 出勤予定時間前
            return f"遅刻中 {late_time.strftime('%H:%M')}出勤予定"
        else:  # 出勤済み
            return "出勤中"

    # 「早退」の場合
    if date_str in work_status["早退"]:
        early_time = datetime.datetime.strptime(work_status["早退"][date_str], "%H:%M").time()
        if now.time() < early_time:  # 早退予定時間前
            return f"{early_time.strftime('%H:%M')}早退予定"
        else:  # 早退済み
            return f"{early_time.strftime('%H:%M')}早退済み"

    # 出勤中の時間帯
    if is_weekday and is_working_hours:
        return "出勤中"

    # 上記以外
    return "勤務外"

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month
    month_days = get_calendar(year, month)
    today_status = get_today_status(today)

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        today=today.day,
        month_days=month_days,
        holidays=holidays,
        work_status=work_status,
        today_status=today_status,
    )

@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays, work_status
    error_message = None  # エラー表示用メッセージ

    if request.method == "POST":
        try:
            action = request.form.get("action")
            date = request.form.get("date")

            if not date:
                error_message = "日付を入力してください。"
                raise ValueError("日付が指定されていません。")

            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

            if action == "add_holiday":
                if date not in holidays:
                    holidays.append(date)
            elif action == "remove_holiday":
                if date in holidays:
                    holidays.remove(date)
            elif action == "add_late":
                late_time = request.form.get("time")
                if late_time:
                    work_status["遅刻"][str(date)] = late_time
            elif action == "remove_late":
                if str(date) in work_status["遅刻"]:
                    del work_status["遅刻"][str(date)]
            elif action == "add_early":
                early_time = request.form.get("time")
                if early_time:
                    work_status["早退"][str(date)] = early_time
            elif action == "remove_early":
                if str(date) in work_status["早退"]:
                    del work_status["早退"][str(date)]

        except Exception as e:
            error_message = f"エラーが発生しました: {str(e)}"

    return render_template("manage.html", holidays=holidays, work_status=work_status, error_message=error_message)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
