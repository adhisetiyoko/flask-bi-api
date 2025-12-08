# config.py
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    
    # Database Config
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "railway")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    
    # CORS Config
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    
    # Flask Config
    DEBUG = os.getenv("FLASK_ENV") != "production"