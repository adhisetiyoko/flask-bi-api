import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # MySQL Configuration
    MYSQL_HOST = (
        os.environ.get("MYSQLHOST") or  # Railway
        os.environ.get("MYSQL_HOST") or  # Local
        "localhost"
    )

    MYSQL_USER = (
        os.environ.get("MYSQLUSER") or 
        os.environ.get("MYSQL_USER") or
        "root"
    )

    MYSQL_PASSWORD = (
        os.environ.get("MYSQLPASSWORD") or 
        os.environ.get("MYSQL_PASSWORD") or
        ""
    )

    MYSQL_DB = (
        os.environ.get("MYSQLDATABASE") or 
        os.environ.get("MYSQL_DB") or
        "simbok_db"
    )

    MYSQL_PORT = int(
        os.environ.get("MYSQLPORT") or 
        os.environ.get("MYSQL_PORT") or
        3306
    )

    MYSQL_CURSORCLASS = 'DictCursor'

    # CORS
    CORS_ORIGINS = ["*"]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

    # Jika ingin override khusus lokal, boleh:
    MYSQL_HOST = os.environ.get("MYSQL_HOST", Config.MYSQL_HOST)
    MYSQL_USER = os.environ.get("MYSQL_USER", Config.MYSQL_USER)
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", Config.MYSQL_PASSWORD)
    MYSQL_DB = os.environ.get("MYSQL_DB", Config.MYSQL_DB)
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", Config.MYSQL_PORT))


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
