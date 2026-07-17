from database.database import (
    get_all_articles
)

for article in get_all_articles():

    title = article[0]
    source = article[1]
    category = article[2]

    print(
        f"{source:15} | "
        f"{category:15} | "
        f"{title}"
    )