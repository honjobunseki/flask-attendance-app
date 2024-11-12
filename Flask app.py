from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 休業日、早退、遅刻の設定（デフォルト値）
holidays = ["2024-11-23", "2024-12-25"]
early_leave_times = {"2024-11-14": "15:00"}
late_arrival_times = {"2024-11-14": "10:00"}

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

@app.route('/')
def calendar_view():
    # 今日の日付と現在の年月を取得
    today = datetime.now().date()
    year = today.year
    month = today.month
    
    # カレンダーのデータを作成
    first_weekday, days_in_month = calendar.monthrange(year, month)
    month_days = []
    for day in range(1, days_in_month + 1):
        date_obj = datetime(year, month, day).date()
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # 日付の状態を判定
        is_today = (date_obj == today)
        is_holiday = (date_str in holidays) or date_obj.weekday() >= 5
        early_leave = early_leave_times.get(date_str)
        late_arrival = late_arrival_times.get(date_str)
        
        # 状態のメッセージ
        status = "出勤中" if is_today and not is_holiday and not early_leave and not late_arrival else ""
        if early_leave:
            status = f"早退: {early_leave}"
        elif late_arrival:
            status = f"遅刻: {late_arrival}"

        month_days.append({"day": day, "is_today": is_today, "is_holiday": is_holiday, "status": status})

    # カレンダーの構造を整える
    calendar_rows = [[]]
    for _ in range(first_weekday):
        calendar_rows[0].append({"day": "", "is_holiday": False, "status": ""})
    for day_info in month_days:
        if len(calendar_rows[-1]) == 7:
            calendar_rows.append([])
        calendar_rows[-1].append(day_info)

    return render_template('calendar.html', month=month, year=year, calendar_rows=calendar_rows)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 休業日追加
        holiday_date = request.form.get('holiday_date')
        if holiday_date and holiday_date not in holidays:
            holidays.append(holiday_date)
        
        # 早退追加
        early_leave_date = request.form.get('early_leave_date')
        early_leave_time = request.form.get('early_leave_time')
        if early_leave_date and early_leave_time:
            early_leave_times[early_leave_date] = early_leave_time
        
        # 遅刻追加
        late_arrival_date = request.form.get('late_arrival_date')
        late_arrival_time = request.form.get('late_arrival_time')
        if late_arrival_date and late_arrival_time:
            late_arrival_times[late_arrival_date] = late_arrival_time
    
    # 休業日、早退、遅刻の管理ページを表示
    return render_template('manage.html', holidays=holidays, early_leave_times=early_leave_times, late_arrival_times=late_arrival_times)

@app.route('/delete', methods=['POST'])
def delete_entry():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    entry_type = request.form.get('entry_type')
    date = request.form.get('date')
    
    if entry_type == "holiday" and date in holidays:
        holidays.remove(date)
    elif entry_type == "early_leave" and date in early_leave_times:
        early_leave_times.pop(date)
    elif entry_type == "late_arrival" and date in late_arrival_times:
        late_arrival_times.pop(date)

    return redirect(url_for('manage'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('manage'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('calendar_view'))
