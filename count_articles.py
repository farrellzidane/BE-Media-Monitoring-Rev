from infrastructure.postgresql_database import (
    close_database_pool,
    database_connection,
)


try:
    with database_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM articles"
        ).fetchone()[0]
    print(count)
finally:
    close_database_pool()
