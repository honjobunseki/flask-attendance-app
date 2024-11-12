from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # セッション用のシークレットキー

# ダミーのログイン情報
USERNAME = "masato"
PASSWORD = "masato2005"

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('manage'))
        else:
            return "ログインに失敗しました。"
    return render_template('login.html')

# 管理ページへのルート
@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        holiday_date = request.form.get('holiday_date')
        late_arrival_time = request.form.get('late_arrival_time')
        early_leaving_time = request.form.get('early_leaving_time')
        # データの保存処理など
        return redirect(url_for('manage'))

    return render_template('manage.html')

# ログアウト機能
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
