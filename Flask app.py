from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 休業日、早退・遅刻の設定
holidays = ["2024-11-23", "2024-12-25"]
early_leave_times = {"2024-11-14": "15:00"}
late_arrival_times = {"2024-11-14": "10:00"}

def get_calendar(year, month):
    """指定された年月のカレンダーを生成し、休業日や早退・遅刻を表示"""
    cal = calendar.monthcalendar(year, month)
    month_days = []
    today_date = datetime.now().date()  # 今日の日付を取得

    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({"day": "", "is_holiday": False, "early_leave": False, "late_arrival": False, "is_today": False, "status": ""})
            else:
                date_obj = datetime(year, month, day).date()
                is_holiday = calendar.weekday(year, month, day) >= 5 or date_obj.strftime("%Y-%m-%d") in holidays
                early_leave = date_obj.strftime("%Y-%m-%d") in early_leave_times
                late_arrival = date_obj.strftime("%Y-%m-%d") in late_arrival_times
                is_today = (date_obj == today_date)
                
                # 「出勤中」のステータス設定
                status = "出勤中" if is_today and not is_holiday and not early_leave and not late_arrival else ""

                week_days.append({
                    "day": day,
                    "is_holiday": is_holiday,
                    "early_leave": early_leave,
                    "late_arrival": late_arrival,
                    "is_today": is_today,
                    "status": status
                })
        month_days.append(week_days)
    
    return month_days

@app.route('/')
def calendar_view():
    # 現在の年月を取得
    today = datetime.today()
    year = today.year
    month = today.month
    month_days = get_calendar(year, month)
    return render_template('calendar.html', month=month, year=year, month_days=month_days)
