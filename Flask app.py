from flask import Flask, render_template
from datetime import datetime
import calendar

app = Flask(__name__)

# 休みの日リスト（例: 祝日）
holidays = ["2024-11-23", "2024-12-25"]  # yyyy-mm-dd形式

def get_calendar(year, month):
    """指定された年月のカレンダーを生成"""
    cal = calendar.monthcalendar(year, month)
    month_days = []
    
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                # 月の空白部分（前月や次月の日付に該当）
                week_days.append({"day": "", "is_holiday": False})
            else:
                # 日付がある場合、土日か祝日を判定
                date_str = f"{year}-{month:02d}-{day:02d}"
                is_holiday = calendar.weekday(year, month, day) >= 5 or date_str in holidays
                week_days.append({"day": day, "is_holiday": is_holiday})
        month_days.append(week_days)
    
    return month_days

@app.route('/')
def calendar_view():
    # 現在の年月を取得
    today = datetime.today()
    year = today.year
    month = today.month

    # 指定月のカレンダーを取得
    month_days = get_calendar(year, month)
    
    return render_template('calendar.html', month=month, year=year, month_days=month_days)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
