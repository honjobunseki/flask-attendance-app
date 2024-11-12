from flask import Flask, render_template
from datetime import datetime, time
import calendar

app = Flask(__name__)

# 休業日、早退、遅刻のデータ
holidays = ["2024-11-23", "2024-12-25"]
early_leave_times = {"2024-11-14": "16:00"}
late_arrival_times = {"2024-11-14": "10:30"}

# 出勤・退勤のデフォルト時間
DEFAULT_START_TIME = time(9, 30)
DEFAULT_END_TIME = time(17, 30)

@app.route('/')
def calendar_view():
    today = datetime.now().date()
    current_time = datetime.now().time()
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
            if is_holiday:
                status = "休業日"
            elif late_arrival and current_time < time.fromisoformat(late_arrival):
                status = f"{late_arrival}出勤予定"
            elif early_leave and current_time >= time.fromisoformat(early_leave):
                status = "早退"
            elif early_leave and current_time < time.fromisoformat(early_leave):
                status = f"{early_leave}早退予定"
            elif DEFAULT_START_TIME <= current_time <= DEFAULT_END_TIME:
                status = "出勤中"
            else:
                status = "退勤時間外"

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
