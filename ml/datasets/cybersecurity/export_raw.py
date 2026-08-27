import sys
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.postgresql_database import database_connection


OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "cybersecurity"
    / "raw.csv"
)


def export_cybersecurity_articles():

    with database_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                title,
                content,
                source,
                category,
                published_date,
                crawl_date,
                url
            FROM articles
            WHERE
                LOWER(category) IN (
                    'cybersecurity',
                    'cyber security',
                    'cybersec',
                    'malware & ransomware',
                    'phishing & social engineering',
                    'data breach & leak',
                    'hacking & cyber crime',
                    'vulnerability & exploit',
                    'ddos & network attack',
                    'cyber espionage & warfare',
                    'security technology & defense',
                    'policy & regulation',
                    'general cybersecurity'
                )
                OR LOWER(title) LIKE '%cyber%'
                OR LOWER(title) LIKE '%siber%'
                OR LOWER(title) LIKE '%ransomware%'
                OR LOWER(title) LIKE '%malware%'
                OR LOWER(title) LIKE '%phishing%'
                OR LOWER(title) LIKE '%hacker%'
                OR LOWER(title) LIKE '%keamanan siber%'
            ORDER BY published_date DESC
            """
        ).fetchall()

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "title",
            "content",
            "source",
            "category",
            "published_date",
            "crawl_date",
            "url"
        ])

        writer.writerows(rows)

    print(
        f"Exported {len(rows)} cybersecurity articles "
        f"to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    export_cybersecurity_articles()