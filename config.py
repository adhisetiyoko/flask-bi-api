# config.py
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    
    # Railway variables (akan auto-resolved oleh Railway)
    MYSQL_HOST = os.getenv("MYSQLHOST") or os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQLUSER") or os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD") or os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQLDATABASE") or os.getenv("MYSQL_DB", "railway")
    MYSQL_PORT = int(os.getenv("MYSQLPORT") or os.getenv("MYSQL_PORT", "3306"))