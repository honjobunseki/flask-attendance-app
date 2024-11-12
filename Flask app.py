from flask import Flask, render_template
from datetime import datetime, time
import os

app = Flask(__name__)

# 勤務時間の設定（例：9時から17時）
WORK_START_TIME = time(9, 0)
WORK_END_TIME = time(17, 0)

# 休業日リスト（例：土日祝や特定の日）
holidays = ["2024-11-23", "2024-12-25"]  # yyyy-mm-dd形式

def is_working_day():
    """現在が勤務日かどうかをチェック"""
    today = datetime.today()
    weekday = today.weekday()  # 0:月曜日, ..., 6:日曜日
    date_str = today.strftime("%Y-%m-%d")
    
    # 土日か祝日であれば休業日と判定
    if weekday >= 5 or date_str in holidays:
        return False
    return True

def is_working_hours():
    """現在が勤務時間内かどうかをチェック"""
    now = datetime.now().time()
    return WORK_START_TIME <= now <= WORK_END_TIME

@app.route('/')
def calendar():
    # 勤務可能かどうかの判定
    can_contact = is_working_day() and is_working_hours()
    return render_template('calendar.html', can_contact=can_contact)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
