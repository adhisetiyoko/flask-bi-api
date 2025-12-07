import pymysql
from app.config.config import config
import os

# Tentukan environment
env = os.getenv("FLASK_ENV", "development")
Config = config.get(env)

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
        return connection
    except Exception as e:
        print("DATABASE CONNECTION ERROR:", e)
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
