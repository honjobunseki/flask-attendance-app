import psycopg2

# データベース接続情報
DATABASE_URL = "postgresql://attendance_management_db_user:vMN7gWhxy8KoHh3m4zzb09BOYyFBcHDe@dpg-ctv212ogph6c73eqfco0-a.oregon-postgres.render.com/attendance_management_db"

# データベース接続
try:
    # データベースに接続
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    print("データベースに接続成功！")

    # 確認用クエリ
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print("PostgreSQL バージョン:", version)

except Exception as e:
    print("データベース接続エラー:", e)

finally:
    # 接続を閉じる
    if 'conn' in locals() and conn:
        conn.close()
