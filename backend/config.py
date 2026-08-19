import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
TEST_DB_NAME = os.getenv("TEST_DB_NAME")

APP_ENV = os.getenv("APP_ENV", "development")

DATABASE_NAME = (
    TEST_DB_NAME if APP_ENV == "test" else DB_NAME
)

print(f"Using database: {DATABASE_NAME} for environment: {APP_ENV}")