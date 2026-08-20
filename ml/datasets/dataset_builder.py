import csv
from pathlib import Path

from database.database import get_all_articles


OUTPUT_DIR = Path("ml/datasets/raw")
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = OUTPUT_DIR / "cybersecurity_news.csv"


def export_dataset():

    articles = get_all_articles()

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "title",
            "content",
            "source",
            "category",
            "published_date"
        ])

        for article in articles:

            writer.writerow([
                article[0],   # title
                article[6],   # content
                article[1],   # source
                article[2],   # category
                article[3]    # published_date
            ])

    print("=" * 60)
    print(f"Exported {len(articles)} articles")
    print(f"Saved to: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    export_dataset()