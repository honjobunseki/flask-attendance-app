from flask import Flask, render_template
from datetime import datetime, date, timedelta
import calendar

app = Flask(__name__)

def generate_calendar(year, month):
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)  # 月曜日始まり
    month_days = cal.monthdayscalendar(year, month)
    return month_days

def is_holiday(year, month, day):
    # 祝日判定ロジック（適宜更新）
    # 必要に応じてデータベースやリストから祝日を判定
    holidays = [
        (2024, 12, 25),  # 例: クリスマス
    ]
    return (year, month, day) in holidays

@app.route("/")
def calendar_view():
    today = datetime.now().day
    year = datetime.now().year
    month = datetime.now().month
    month_days = generate_calendar(year, month)
    return render_template(
        "calendar.html",
        year=year,
        month=month,
        month_days=month_days,
        today=today,
        is_holiday=is_holiday,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
