from urllib.parse import urlparse

from infrastructure.postgresql_database import database_connection


DEFAULT_SOURCES = (
    ("The Hacker News", "https://thehackernews.com/"),
    ("SecurityWeek", "https://www.securityweek.com/"),
    ("Cybersecurity News", "https://cybersecuritynews.com/"),
    ("Cybersecurity Dive", "https://www.cybersecuritydive.com/"),
    ("BleepingComputer", "https://www.bleepingcomputer.com/"),
    ("Dark Reading", "https://www.darkreading.com/"),
    ("KrebsOnSecurity", "https://krebsonsecurity.com/"),
    ("The Record", "https://therecord.media/"),
    ("Help Net Security", "https://www.helpnetsecurity.com/"),
    ("Infosecurity Magazine", "https://www.infosecurity-magazine.com/"),
)


def _source_name(url):
    hostname = urlparse(url).hostname or url
    return hostname.removeprefix("www.").split(".")[0].replace("-", " ").title()


def initialize_defaults():
    with database_connection() as connection:
        for name, url in DEFAULT_SOURCES:
            connection.execute(
                """
                INSERT INTO monitored_sources (name, url)
                VALUES (%s, %s)
                ON CONFLICT (url) DO NOTHING
                """,
                (name, url),
            )


def get_settings():
    with database_connection() as connection:
        settings = connection.execute(
            "SELECT crawl_enabled, crawl_interval_minutes FROM monitoring_settings WHERE id = 1"
        ).fetchone()
        sources = connection.execute(
            "SELECT id, name, url, enabled FROM monitored_sources ORDER BY name"
        ).fetchall()
        keywords = connection.execute(
            "SELECT id, keyword, enabled FROM monitored_keywords ORDER BY keyword"
        ).fetchall()

    return {
        "crawl_enabled": bool(settings[0]),
        "crawl_interval_minutes": settings[1],
        "sources": [
            {"id": row[0], "name": row[1], "url": row[2], "enabled": row[3]}
            for row in sources
        ],
        "keywords": [
            {"id": row[0], "keyword": row[1], "enabled": row[2]}
            for row in keywords
        ],
    }


def update_crawl_settings(crawl_enabled, crawl_interval_minutes):
    if crawl_interval_minutes not in {15, 30, 60, 120, 360}:
        raise ValueError("Interval crawl harus 15, 30, 60, 120, atau 360 menit.")
    with database_connection() as connection:
        connection.execute(
            """
            UPDATE monitoring_settings
            SET crawl_enabled = %s, crawl_interval_minutes = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (crawl_enabled, crawl_interval_minutes),
        )
    return get_settings()


def add_source(name, url):
    clean_url = url.strip().rstrip("/") + "/"
    parsed = urlparse(clean_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL sumber harus berupa URL HTTP atau HTTPS yang valid.")
    with database_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO monitored_sources (name, url)
            VALUES (%s, %s)
            ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, enabled = TRUE
            RETURNING id, name, url, enabled
            """,
            (name.strip() or _source_name(clean_url), clean_url),
        ).fetchone()
    return {"id": row[0], "name": row[1], "url": row[2], "enabled": row[3]}


def remove_source(source_id):
    with database_connection() as connection:
        row = connection.execute("DELETE FROM monitored_sources WHERE id = %s RETURNING id", (source_id,)).fetchone()
    return row is not None


def add_keyword(keyword):
    clean_keyword = keyword.strip().lower()
    if len(clean_keyword) < 2:
        raise ValueError("Keyword minimal terdiri dari 2 karakter.")
    with database_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO monitored_keywords (keyword)
            VALUES (%s)
            ON CONFLICT (keyword) DO UPDATE SET enabled = TRUE
            RETURNING id, keyword, enabled
            """,
            (clean_keyword,),
        ).fetchone()
    return {"id": row[0], "keyword": row[1], "enabled": row[2]}


def remove_keyword(keyword_id):
    with database_connection() as connection:
        row = connection.execute("DELETE FROM monitored_keywords WHERE id = %s RETURNING id", (keyword_id,)).fetchone()
    return row is not None


def get_custom_sources():
    with database_connection() as connection:
        return connection.execute(
            "SELECT name, url FROM monitored_sources WHERE enabled = TRUE ORDER BY id"
        ).fetchall()


def get_enabled_keywords():
    try:
        with database_connection() as connection:
            return [
                row[0]
                for row in connection.execute(
                    "SELECT keyword FROM monitored_keywords WHERE enabled = TRUE ORDER BY id"
                ).fetchall()
            ]
    except RuntimeError:
        return []