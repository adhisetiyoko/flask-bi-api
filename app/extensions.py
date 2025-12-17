# app/extensions.py
from flask_mysqldb import MySQL
from flask_cors import CORS

# Initialize extensions
mysql = MySQL()
cors = CORS()