from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ホームページ
@app.route('/')
def index():
    return "出勤カレンダーへようこそ！"

# 管理ページ（休業日、遅刻・早退日時の編集フォーム）へのルート
@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if request.method == 'POST':
        # POSTデータを処理して保存する（例: データベースに保存）
        holiday_date = request.form.get('holiday_date')
        late_arrival_time = request.form.get('late_arrival_time')
        early_leaving_time = request.form.get('early_leaving_time')

        # 必要な処理やデータベース保存をここで実行
        # 例: save_holiday(holiday_date)
        #     save_late_arrival(late_arrival_time)
        #     save_early_leaving(early_leaving_time)

        # データ保存後、同じページにリダイレクト
        return redirect(url_for('manage'))

    # GETリクエスト時に編集フォームページを表示
    return render_template('manage.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
