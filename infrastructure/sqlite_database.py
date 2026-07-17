import sqlite3
from contextlib import contextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_FILE = DATA_DIR / "articles.db"


@contextmanager
def database_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)

    try:
        yield connection
    finally:
        connection.close()


def initialize_database():
    with database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT UNIQUE,
                source TEXT,
                category TEXT,
                published_date TEXT,
                crawl_date TEXT,
                content TEXT
            )
            """
        )
        connection.commit()
