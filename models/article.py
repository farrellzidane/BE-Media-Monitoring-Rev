from dataclasses import dataclass, field
from datetime import datetime


def current_crawl_date():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Article:
    title: str
    url: str
    source: str
    category: str
    published_date: str
    content: str

    crawl_date: str = field(default_factory=current_crawl_date)
