import pyodbc
from config import (
    AUTH_DB_DRIVER, AUTH_DB_SERVER, AUTH_DB_NAME,
    AUTH_DB_USERNAME, AUTH_DB_PASSWORD,
    INFO_DB_DRIVER, INFO_DB_SERVER, INFO_DB_NAME,
    INFO_DB_USERNAME, INFO_DB_PASSWORD
)

def get_auth_db_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={AUTH_DB_DRIVER};"
            f"SERVER={AUTH_DB_SERVER};"
            f"DATABASE={AUTH_DB_NAME};"
            f"UID={AUTH_DB_USERNAME};"
            f"PWD={AUTH_DB_PASSWORD};"
            "TrustServerCertificate=yes;"
            "Connection Timeout=5;"
        )
        return conn
    except pyodbc.Error as e:
        raise ConnectionError(f"Authentication database connection failed: {e}")

def get_info_db_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={INFO_DB_DRIVER};"
            f"SERVER={INFO_DB_SERVER};"
            f"DATABASE={INFO_DB_NAME};"
            f"UID={INFO_DB_USERNAME};"
            f"PWD={INFO_DB_PASSWORD};"
            "TrustServerCertificate=yes;"
            "Connection Timeout=5;"
        )
        return conn
    except pyodbc.Error as e:
        raise ConnectionError(f"Information database connection failed: {e}")
