from flask import Flask, render_template
import calendar
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def calendar_view():
    # 現在の年月
    now = datetime.now()
    year = now.year
    month = now.month
    today = now.day

    # 月のカレンダー情報を取得
    cal = calendar.Calendar(firstweekday=6)  # 日曜日開始
    month_days = list(cal.itermonthdays2(year, month))  # [(日付, 曜日)] のタプルリスト
    weeks = [[]]
    
    # 日付を週ごとに整形
    for day, weekday in month_days:
        if day == 0:  # 空白の日付
            weeks[-1].append((None, weekday))
        else:
            weeks[-1].append((day, weekday))
        if weekday == 5:  # 土曜日で行を切り替え
            weeks.append([])

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        today=today,
        weeks=weeks,
    )

if __name__ == "__main__":
    app.run(debug=True)
