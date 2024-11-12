from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, time
import calendar

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 休業日、早退・遅刻の設定（デフォルト値）
holidays = ["2024-11-23", "2024-12-25"]
early_leave_times = {"2024-11-14": "15:00"}
late_arrival_times = {"2024-11-14": "10:00"}

# 簡単なログイン情報
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

def get_calendar(year, month):
    """指定された年月のカレンダーを生成し、休業日や早退・遅刻を表示"""
    cal = calendar.monthcalendar(year, month)
    month_days = []
    
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({"day": "", "is_holiday": False, "early_leave": False, "late_arrival": False})
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                is_holiday = calendar.weekday(year, month, day) >= 5 or date_str in holidays
                early_leave = date_str in early_leave_times
                late_arrival = date_str in late_arrival_times
                week_days.append({"day": day, "is_holiday": is_holiday, "early_leave": early_leave, "late_arrival": late_arrival})
        month_days.append(week_days)
    
    return month_days

@app.route('/')
def calendar_view():
    today = datetime.today()
    year = today.year
    month = today.month
    month_days = get_calendar(year, month)
    return render_template('calendar.html', month=month, year=year, month_days=month_days)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 休業日追加
        holiday_date = request.form.get('holiday_date')
        if holiday_date and holiday_date not in holidays:
            holidays.append(holiday_date)
        
        # 早退時間追加
        early_leave_date = request.form.get('early_leave_date')
        early_leave_time = request.form.get('early_leave_time')
        if early_leave_date and early_leave_time:
            early_leave_times[early_leave_date] = early_leave_time
        
        # 遅刻時間追加
        late_arrival_date = request.form.get('late_arrival_date')
        late_arrival_time = request.form.get('late_arrival_time')
        if late_arrival_date and late_arrival_time:
            late_arrival_times[late_arrival_date] = late_arrival_time

    return render_template('manage.html', holidays=holidays, early_leave_times=early_leave_times, late_arrival_times=late_arrival_times)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
