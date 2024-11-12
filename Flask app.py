from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime, timedelta
import jpholiday

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションの暗号化キー

DATABASE = 'holidays.db'

# 認証情報
USERNAME = 'masato'
PASSWORD = 'masato2005'

def query_db(query, args=(), one=False):
    """データベースのクエリ実行"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def get_holidays():
    """休業日を取得"""
    holidays = query_db("SELECT date FROM holidays")
    return [h[0] for h in holidays]

def get_early_leaving():
    """早退時間を取得"""
    early_leaving = query_db("SELECT date, time FROM early_leaving")
    return {e[0]: e[1] for e in early_leaving}

def get_late_arrival():
    """遅刻時間を取得"""
    late_arrival = query_db("SELECT date, time FROM late_arrival")
    return {l[0]: l[1] for l in late_arrival}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('manage'))
        else:
            return "ログイン失敗しました。ユーザー名またはパスワードが間違っています。"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    current_year = datetime.now().year
    current_month = datetime.now().month
    holidays = get_holidays()
    early_leaving = get_early_leaving()
    late_arrival = get_late_arrival()

    first_weekday = datetime(current_year, current_month, 1).weekday()
    num_days = (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).day

    return render_template(
        'calendar.html', holidays=holidays, early_leaving=early_leaving, 
        late_arrival=late_arrival, year=current_year, month=current_month, 
        first_weekday=first_weekday, num_days=num_days
    )

@app.route('/manage')
def manage():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    holidays = get_holidays()
    early_leaving = get_early_leaving()
    late_arrival = get_late_arrival()
    return render_template('manage.html', holidays=holidays, early_leaving=early_leaving, late_arrival=late_arrival)

@app.route('/add_holiday', methods=['POST'])
def add_holiday():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    date = request.form['date']
    query_db("INSERT OR IGNORE INTO holidays (date) VALUES (?)", [date])
    return redirect(url_for('manage'))

@app.route('/add_early_leaving', methods=['POST'])
def add_early_leaving():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    date = request.form['date']
    time = request.form['time']
    query_db("INSERT OR REPLACE INTO early_leaving (date, time) VALUES (?, ?)", [date, time])
    return redirect(url_for('manage'))

@app.route('/add_late_arrival', methods=['POST'])
def add_late_arrival():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    date = request.form['date']
    time = request.form['time']
    query_db("INSERT OR REPLACE INTO late_arrival (date, time) VALUES (?, ?)", [date, time])
    return redirect(url_for('manage'))

@app.route('/delete_holiday', methods=['POST'])
def delete_holiday():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    date = request.form['date']
    query_db("DELETE FROM holidays WHERE date = ?", [date])
    return redirect(url_for('manage'))

@app.route('/delete_early_leaving', methods=['POST'])
def delete_early_leaving():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    date = request.form['date']
    query_db("DELETE FROM early_leaving WHERE date = ?", [date])
    return redirect(url_for('manage'))

@app.route('/delete_late_arrival', methods=['POST'])
def delete_late_arrival():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    date = request.form['date']
    query_db("DELETE FROM late_arrival WHERE date = ?", [date])
    return redirect(url_for('manage'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
