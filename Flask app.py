from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import calendar

app = Flask(__name__)

# カレンダー表示のためのルート
@app.route("/")
def calendar_page():
    # 今日の日付を取得
    today = datetime.now()
    year, month = today.year, today.month

    # カレンダーを生成
    cal = calendar.Calendar(firstweekday=6)  # 日曜日を週の始まりとする
    month_days = list(cal.itermonthdays2(year, month))  # 日付と曜日のタプルをリストで取得

    # 祝日や特別な日をここで定義可能（例: 日本の祝日をリスト化）
    holidays = [
        datetime(2024, 1, 1),  # 元日
        datetime(2024, 11, 23),  # 勤労感謝の日
    ]

    # データをテンプレートに渡す
    return render_template(
        "calendar.html",
        today=today,
        year=year,
        month=month,
        month_days=month_days,
        holidays=holidays,
    )

# 祝日編集ページ
@app.route("/manage", methods=["GET", "POST"])
def manage_holidays():
    if request.method == "POST":
        # 新しい祝日を追加する処理
        new_date = request.form.get("holiday")
        if new_date:
            # holidays.txtに追加する（永続化用）
            with open("holidays.txt", "a") as file:
                file.write(new_date + "\n")
        return redirect(url_for("manage_holidays"))

    # holidays.txtから現在の祝日リストを取得
    try:
        with open("holidays.txt", "r") as file:
            holidays = file.read().splitlines()
    except FileNotFoundError:
        holidays = []

    return render_template("manage.html", holidays=holidays)

# 祝日削除
@app.route("/delete_holiday", methods=["POST"])
def delete_holiday():
    holiday_to_delete = request.form.get("delete_holiday")
    if holiday_to_delete:
        with open("holidays.txt", "r") as file:
            holidays = file.read().splitlines()
        # 指定された祝日を削除
        holidays = [h for h in holidays if h != holiday_to_delete]
        with open("holidays.txt", "w") as file:
            file.write("\n".join(holidays) + "\n")
    return redirect(url_for("manage_holidays"))

if __name__ == "__main__":
    app.run(debug=True)
