import psycopg
from backend.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DATABASE_NAME

def get_connection():
    return psycopg.connect(
        host = DB_HOST,
        port = DB_PORT,
        dbname = DATABASE_NAME,
        user = DB_USER,
        password = DB_PASSWORD
    )