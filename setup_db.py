import os
import psycopg2
from psycopg2.extras import DictCursor
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベース接続設定
DATABASE_URL = os.environ.get("DATABASE_URL")

def setup_database():
    if not DATABASE_URL:
        logger.error("DATABASE_URL is not set.")
        raise Exception("DATABASE_URL is not set.")
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        # 必要なテーブルを作成
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(150) NOT NULL
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            date DATE NOT NULL,
            status VARCHAR(20) NOT NULL
        );
        """)
        conn.commit()
        logger.info("Database setup completed successfully.")
    except Exception as e:
        logger.error(f"Error setting up the database: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    setup_database()
