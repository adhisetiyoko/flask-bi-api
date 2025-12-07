import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # MySQL dari Railway
    MYSQL_HOST = os.environ.get("MYSQLHOST")
    MYSQL_USER = os.environ.get("MYSQLUSER")
    MYSQL_PASSWORD = os.environ.get("MYSQLPASSWORD")
    MYSQL_DB = os.environ.get("MYSQLDATABASE")
    MYSQL_PORT = int(os.environ.get("MYSQLPORT", 3306))
    
    # CORS
    CORS_ORIGINS = ["*"]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # Jika run lokal → MySQL lokal
    MYSQL_HOST = os.environ.get("MYSQL_HOST") or 'localhost'
    MYSQL_USER = os.environ.get("MYSQL_USER") or 'root'
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD") or ''
    MYSQL_DB = os.environ.get("MYSQL_DB") or 'simbok_db'
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
