from dataclasses import dataclass
from datetime import datetime
@dataclass
class Article:
    title: str
    url: str
    source: str
    category: str
    published_date: str
    content: str

    crawl_date: str = (
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )