import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "switchback.proxy.rlwy.net")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "pZPecHJjNLcZENpzjNNIIoVtNvBWdPOA")
    MYSQL_DB = os.getenv("MYSQL_DB", "railway")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 48397))
