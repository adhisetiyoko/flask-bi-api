import pymysql
import os
import sys

# Tambahkan root project ke sys.path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from config import Config

# DEBUG: Print config values
print("="*50)
print("DATABASE CONFIG DEBUG:")
print(f"MYSQL_HOST: {Config.MYSQL_HOST}")
print(f"MYSQL_USER: {Config.MYSQL_USER}")
print(f"MYSQL_DB: {Config.MYSQL_DB}")
print(f"MYSQL_PORT: {Config.MYSQL_PORT}")
print(f"MYSQL_PASSWORD: {'*' * len(Config.MYSQL_PASSWORD) if Config.MYSQL_PASSWORD else 'NOT SET'}")
print("="*50)

def get_db_connection():
    """Membuat koneksi database MySQL berdasarkan config"""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Database connection successful!")
        return connection
    except Exception as e:
        print("❌ DATABASE CONNECTION ERROR:", e)
        return None

def query(sql, params=None):
    """SELECT query"""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
        return result
    finally:
        conn.close()

def execute(sql, params=None):
    """INSERT/UPDATE/DELETE"""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        print("DATABASE EXECUTION ERROR:", e)
        return False
    finally:
        conn.close()