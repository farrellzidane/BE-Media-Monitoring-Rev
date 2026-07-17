from database.database import (
    get_all_articles
)

articles = get_all_articles()

for article in articles:

    title = article[0]
    source = article[1]
    date = article[3]

    if date != "2026-06-15":

        print()
        print(
            f"DATE: {date}"
        )

        print(
            f"SOURCE: {source}"
        )

        print(
            f"TITLE: {title}"
        )