import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# デフォルトの休日設定
holidays = ["2024-11-23", "2024-12-31"]

# 出勤設定
default_start_time = "09:30"
default_end_time = "17:30"

@app.route("/")
def calendar():
    today = "2024-11-12"  # 実際は動的に取得: str(datetime.date.today())
    return render_template(
        "calendar.html",
        holidays=holidays,
        today=today,
        start_time=default_start_time,
        end_time=default_end_time
    )

@app.route("/manage", methods=["GET", "POST"])
def manage():
    global holidays
    if request.method == "POST":
        action = request.form.get("action")
        date = request.form.get("date")
        if action == "add" and date:
            holidays.append(date)
            holidays = list(set(holidays))  # 重複を排除
        elif action == "remove" and date:
            holidays = [h for h in holidays if h != date]
        return redirect(url_for("manage"))
    return render_template("manage.html", holidays=holidays)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
