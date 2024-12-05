from flask import Flask, render_template
import calendar
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    # 現在の年月を取得
    now = datetime.now()
    year = now.year
    month = now.month

    # カレンダーを生成
    cal = calendar.Calendar(firstweekday=0)  # 月曜日から開始
    month_days = cal.monthdayscalendar(year, month)  # 日付を週ごとにリスト化
    month_name = calendar.month_name[month]  # 月名

    return render_template("calendar.html", year=year, month=month, month_name=month_name, month_days=month_days)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
