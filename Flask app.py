from flask import Flask, render_template
from datetime import datetime, timedelta
import calendar
import jpholiday

app = Flask(__name__)

def generate_calendar(year, month):
    """指定された年と月のカレンダーを作成"""
    cal = calendar.Calendar(firstweekday=6)  # 日曜日開始
    month_days = cal.monthdayscalendar(year, month)
    today = datetime.now()
    holidays = [day for day in range(1, 32) if jpholiday.is_holiday(datetime(year, month, day))]

    # 日付のスタイルデータを準備
    styled_days = []
    for week in month_days:
        styled_week = []
        for day in week:
            if day == 0:
                styled_week.append({"day": "", "class": "empty"})
            elif day == today.day and year == today.year and month == today.month:
                styled_week.append({"day": day, "class": "today"})
            elif day in holidays:
                styled_week.append({"day": day, "class": "holiday"})
            else:
                styled_week.append({"day": day, "class": ""})
        styled_days.append(styled_week)
    return styled_days

@app.route("/")
def index():
    """カレンダー表示"""
    today = datetime.now()
    year = today.year
    month = today.month
    calendar_data = generate_calendar(year, month)
    return render_template("calendar.html", calendar_data=calendar_data, year=year, month=month)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render用のポート設定
    app.run(host="0.0.0.0", port=port)
