import os
os.environ["APP_ENV"] = "test"
import pytest
import psycopg
from pathlib import Path
from backend.config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DATABASE_NAME)

def get_test_connection():
    return psycopg.connect(
        host = DB_HOST,
        port = DB_PORT,
        dbname = DATABASE_NAME,
        user = DB_USER,
        password = DB_PASSWORD
    )


@pytest.fixture
def reset_test_database():
    seed_sql = Path("database/test_seed.sql").read_text()
    with get_test_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(seed_sql)
