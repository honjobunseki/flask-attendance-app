import sqlite3

# データベースの作成と初期化
conn = sqlite3.connect('holidays.db')
cursor = conn.cursor()

# 休日テーブルの作成
cursor.execute('''
CREATE TABLE IF NOT EXISTS holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL
)
''')

conn.commit()
conn.close()
print("データベースがセットアップされました。")
