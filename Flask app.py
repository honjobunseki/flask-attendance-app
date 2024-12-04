from flask import Flask, render_template, request, Response
from datetime import datetime, time
import sqlite3
import calendar

app = Flask(__name__)

# データベース接続ヘルパー
def get_db_connection():
    conn = sqlite3.connect('holidays.db')
    conn.row_factory = sqlite3.Row
    return conn

# 出勤・退勤のデフォルト時間
DEFAULT_START_TIME = time(9, 30)
DEFAULT_END_TIME = time(17, 30)

# カレンダーページ
@app.route('/')
def calendar_view():
    today = datetime.now().date()
    current_time = datetime.now().time()
    year = today.year
    month = today.month

    # データベースから休日を取得
    conn = get_db_connection()
    holidays = [row['date'] for row in conn.execute('SELECT date FROM holidays').fetchall()]
    conn.close()

    # カレンダー生成
    first_weekday, days_in_month = calendar.monthrange(year, month)
    days = []
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month, day).date()
        date_str = date_obj.strftime("%Y-%m-%d")
        is_holiday = date_str in holidays or date_obj.weekday() >= 5  # 休日か土日

        status = ""
        if date_obj == today:
            if is_holiday:
                status = "休業日"
            elif DEFAULT_START_TIME <= current_time <= DEFAULT_END_TIME:
                status = "出勤中"
            else:
                status = "退勤時間外"

        days.append({"day": day, "is_holiday": is_holiday, "status": status})

    # カレンダーを行列形式に整える
    calendar_rows = [[]]
    for _ in range(first_weekday):
        calendar_rows[0].append({"day": "", "is_holiday": False, "status": ""})
    for day in days:
        if len(calendar_rows[-1]) == 7:
            calendar_rows.append([])
        calendar_rows[-1].append(day)

    return render_template('calendar.html', year=year, month=month, calendar_rows=calendar_rows)

# 休日管理ページ
@app.route('/manage', methods=['GET', 'POST'])
def manage_holidays():
    auth = request.authorization
    if not auth or not (auth.username == "masato" and auth.password == "masato2005"):
        return Response(
            "管理ページにアクセスするにはログインが必要です。", 401,
            {"WWW-Authenticate": "Basic realm='Login Required'"}
        )

    conn = get_db_connection()
    if request.method == 'POST':
        date = request.form['date']
        action = request.form['action']
        if action == 'add':
            conn.execute('INSERT OR IGNORE INTO holidays (date) VALUES (?)', (date,))
        elif action == 'delete':
            conn.execute('DELETE FROM holidays WHERE date = ?', (date,))
        conn.commit()

    holidays = conn.execute('SELECT * FROM holidays').fetchall()
    conn.close()
    return render_template('manage.html', holidays=holidays)

if __name__ == '__main__':
    app.run(debug=True)
