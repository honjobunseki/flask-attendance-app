import os
from flask import Flask, render_template, request
from datetime import datetime, timedelta
import calendar
import jpholiday

app = Flask(__name__)

# カレンダー生成関数
def generate_calendar(year, month):
    calendar.setfirstweekday(calendar.SUNDAY)  # カレンダーを日曜始まりに設定
    month_days = calendar.monthcalendar(year, month)
    today = datetime.now().day if year == datetime.now().year and month == datetime.now().month else None
    return month_days, today

# 祝日判定関数
def is_holiday(year, month, day):
    return jpholiday.is_holiday_name(datetime(year, month, day)) is not None

@app.route("/")
def index():
    # 現在の年月
    now = datetime.now()
    year = now.year
    month = now.month

    # カレンダー生成
    month_days, today = generate_calendar(year, month)

    # カレンダーデータをテンプレートに渡す
    return render_template("calendar.html", year=year, month=month, month_days=month_days, today=today, is_holiday=is_holiday)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    # 管理ページ（祝日や勤務時間を管理）
    if request.method == "POST":
        # 必要に応じてリクエスト処理
        pass

    # 祝日一覧（仮）
    holidays = ["2024-12-25", "2024-12-31"]  # 仮のデータ、実際はデータベースから取得
    return render_template("manage.html", holidays=holidays)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Renderで使用するポート
    app.run(host="0.0.0.0", port=port)
