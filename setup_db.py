import sqlite3

DB_PATH = "holidays.db"

# Initialize the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create holidays table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE
    )
''')

conn.commit()
conn.close()

print("Database initialized.")
