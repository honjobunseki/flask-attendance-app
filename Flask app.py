from flask import Flask, render_template, request, jsonify
import datetime
import pytz
import os

app = Flask(__name__)

@app.route("/")
def calendar():
    today = datetime.date.today()
    year, month = today.year, today.month

    # カレンダーの日付データを生成
    first_day = datetime.date(year, month, 1)
    last_day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)) if month < 12 else datetime.date(year, 12, 31)
    month_days = []
    week = []
    current_date = first_day

    while current_date.weekday() != 0:
        week.append((0, "", False))  # 空白セル
        current_date -= datetime.timedelta(days=1)

    current_date = first_day
    while current_date <= last_day:
        is_holiday = current_date.weekday() >= 5  # 土日は祝日扱い
        week.append((current_date.day, "", is_holiday))
        if len(week) == 7:
            month_days.append(week)
            week = []
        current_date += datetime.timedelta(days=1)

    while len(week) < 7:
        week.append((0, "", False))  # 空白セル
    if week:
        month_days.append(week)

    return render_template("calendar.html", year=year, month=month, today=today.day, month_days=month_days)

@app.route("/popup")
def popup():
    day = request.args.get("day")
    return f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <title>連絡する - {day}</title>
    </head>
    <body>
        <h1>{day} の連絡事項</h1>
        <form method="post" action="/send-email">
            <label>件名: <input type="text" name="subject" value="{day}の連絡事項"></label><br><br>
            <label>本文:</label><br>
            <textarea name="body" rows="10" cols="30">詳細を記入してください。</textarea><br><br>
            <button type="submit">送信する</button>
        </form>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
