from flask import Flask, render_template, session, redirect, url_for, request
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# サンプルの休業日、早退、遅刻データ
holidays = ["2024-11-23", "2024-12-25"]
early_leave_times = {"2024-11-14": "15:00"}
late_arrival_times = {"2024-11-14": "10:00"}

@app.route('/')
def calendar_view():
    # 今日の日付と現在の年月を取得
    today = datetime.now().date()
    year = today.year
    month = today.month
    
    # カレンダーのデータを作成
    first_weekday, days_in_month = calendar.monthrange(year, month)
    month_days = []
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month, day).date()
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # 日付の状態を判定
        is_today = (date_obj == today)
        is_holiday = (date_str in holidays) or date_obj.weekday() >= 5
        early_leave = early_leave_times.get(date_str)
        late_arrival = late_arrival_times.get(date_str)
        
        # 状態のメッセージ
        status = ""
        if is_today:
            if not is_holiday and not early_leave and not late_arrival:
                status = "出勤中"
            elif early_leave:
                status = f"早退: {early_leave}"
            elif late_arrival:
                status = f"遅刻: {late_arrival}"

        month_days.append({"day": day, "is_today": is_today, "is_holiday": is_holiday, "status": status})

    # カレンダーの構造を整える
    calendar_rows = [[]]
    for _ in range(first_weekday):
        calendar_rows[0].append({"day": "", "is_holiday": False, "status": ""})
    for day_info in month_days:
        if len(calendar_rows[-1]) == 7:
            calendar_rows.append([])
        calendar_rows[-1].append(day_info)

    return render_template('calendar.html', month=month, year=year, calendar_rows=calendar_rows)
