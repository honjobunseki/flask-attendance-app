from flask import Flask, render_template
import calendar
import jpholiday
import json
from datetime import date, datetime

app = Flask(__name__)

def load_data():
    """JSONファイルからデータを読み込む"""
    with open("holidays.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def calendar_view():
    today = date.today()
    year, month = today.year, today.month

    # JSONデータをロード
    data = load_data()
    holidays = data.get("holidays", [])
    working_hours = data.get("working_hours", {})

    # カレンダーの生成
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.itermonthdays4(year, month)
    days = []

    for day_tuple in month_days:
        year, month, day, weekday = day_tuple
        if month == today.month:
            is_today = today.day == day
            full_date = f"{year:04d}-{month:02d}-{day:02d}"
            is_holiday = full_date in holidays or jpholiday.is_holiday(datetime(year, month, day))

            # 勤務時間
            custom_hours = working_hours.get("custom", {}).get(full_date, working_hours.get("default"))
            hours = f"{custom_hours['start']}〜{custom_hours['end']}" if not is_holiday else "休み"

            days.append({
                "day": day,
                "is_today": is_today,
                "is_holiday": is_holiday,
                "hours": hours
            })

    return render_template("calendar.html", year=year, month=month, days=days)

if __name__ == "__main__":
    app.run(debug=True)
