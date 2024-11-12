import sqlite3

def setup_database():
    conn = sqlite3.connect('holidays.db')
    cursor = conn.cursor()

    # 休業日テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY,
            date TEXT UNIQUE NOT NULL
        )
    ''')

    # 早退時間テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS early_leaving (
            id INTEGER PRIMARY KEY,
            date TEXT UNIQUE NOT NULL,
            time TEXT NOT NULL
        )
    ''')

    # 遅刻時間テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS late_arrival (
            id INTEGER PRIMARY KEY,
            date TEXT UNIQUE NOT NULL,
            time TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

setup_database()
