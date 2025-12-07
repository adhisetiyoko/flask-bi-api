import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # MySQL Configuration - Railway format
    MYSQL_HOST = os.environ.get("MYSQLHOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQLUSER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQLPASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQLDATABASE", "simbok_db")
    MYSQL_PORT = int(os.environ.get("MYSQLPORT", 3306))
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # CORS
    CORS_ORIGINS = ["*"]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
    # Override untuk development lokal
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "simbok_db")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}