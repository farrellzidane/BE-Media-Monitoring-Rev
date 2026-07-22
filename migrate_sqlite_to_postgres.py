import argparse
import sqlite3

from contextlib import closing
from pathlib import Path

from infrastructure.postgresql_database import (
    close_database_pool,
    database_connection,
    initialize_database,
)


DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent / "data" / "articles.db"


def read_sqlite_articles(sqlite_path):
    sqlite_path = Path(sqlite_path).resolve()
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")

    connection_uri = f"file:{sqlite_path.as_posix()}?mode=ro"
    with closing(sqlite3.connect(connection_uri, uri=True)) as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                title,
                url,
                source,
                category,
                published_date,
                crawl_date,
                content
            FROM articles
            ORDER BY id
            """
        ).fetchall()
        unique_urls = connection.execute(
            "SELECT COUNT(DISTINCT url) FROM articles"
        ).fetchone()[0]

    return rows, unique_urls


def migrate(sqlite_path=DEFAULT_SQLITE_PATH):
    rows, source_unique_urls = read_sqlite_articles(sqlite_path)
    initialize_database()

    with database_connection() as connection:
        existing_rows = connection.execute(
            "SELECT COUNT(*) FROM articles"
        ).fetchone()[0]
        if existing_rows:
            raise RuntimeError(
                "PostgreSQL articles table is not empty; migration was not run."
            )

        if rows:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO articles (
                        id,
                        title,
                        url,
                        source,
                        category,
                        published_date,
                        crawl_date,
                        content
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    rows,
                )

        target_rows, target_unique_urls = connection.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT url)
            FROM articles
            """
        ).fetchone()

        if target_rows != len(rows) or target_unique_urls != source_unique_urls:
            raise RuntimeError(
                "Migration verification failed; PostgreSQL transaction was rolled back."
            )

        connection.execute(
            """
            SELECT setval(
                pg_get_serial_sequence('articles', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            )
            FROM articles
            """
        )

    return {
        "rows": len(rows),
        "unique_urls": source_unique_urls,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Migrate an SQLite articles database to empty PostgreSQL."
    )
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=DEFAULT_SQLITE_PATH,
        help="Path to the source SQLite database.",
    )
    args = parser.parse_args()

    try:
        result = migrate(args.sqlite_path)
    finally:
        close_database_pool()

    print(
        "Migration complete: "
        f"{result['rows']} rows, {result['unique_urls']} unique URLs."
    )


if __name__ == "__main__":
    main()
