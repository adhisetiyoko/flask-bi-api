# config.py
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    
    # Railway MySQL Variables (sudah benar!)
    MYSQL_HOST = os.getenv("MYSQLHOST", "localhost")
    MYSQL_USER = os.getenv("MYSQLUSER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD", "")
    MYSQL_DB = os.getenv("MYSQLDATABASE", "railway")
    MYSQL_PORT = int(os.getenv("MYSQLPORT", "3306"))
    
    # Debug
    @staticmethod
    def print_debug():
        print("=" * 70)
        print("DATABASE CONFIG:")
        print(f"Host     : {Config.MYSQL_HOST}")
        print(f"User     : {Config.MYSQL_USER}")
        print(f"Database : {Config.MYSQL_DB}")
        print(f"Port     : {Config.MYSQL_PORT}")
        print(f"Password : {'***' if Config.MYSQL_PASSWORD else 'NOT SET'}")
        print("=" * 70)