from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CNN_URLS = [
    "https://www.cnnindonesia.com/ekonomi"
]

DETIK_URLS = [
    "https://finance.detik.com"
]

KOMPAS_URL = "https://money.kompas.com"
TEMPO_URL = "https://www.tempo.co/ekonomi"


CNBC_URLS = [
    "https://www.cnbcindonesia.com/market",
    "https://www.cnbcindonesia.com/news",
    "https://www.cnbcindonesia.com/tech",
    "https://www.cnbcindonesia.com/entrepreneur"
]
LIPUTAN6_URL = "https://www.liputan6.com"
KUMPARAN_URL = "https://kumparan.com"
OKEZONE_URLS = [
    "https://economy.okezone.com"
]
SINDONEWS_URLS = [
    "https://ekbis.sindonews.com"
]
TRIBUN_URLS = [
    "https://www.tribunnews.com"
]
KUMPARAN_GRAPHQL_URL = (
    "https://cdn-graphql-v4.kumparan.com/query"
)

MAX_ARTICLES = 30

REQUEST_TIMEOUT = 20

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)

OUTPUT_FILE = str(DATA_DIR / "articles.json")

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,"
        "image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}


# Data-quality rules are normalized percentages. The weights below intentionally
# total 100 so the API can expose an explainable 0-100 score regardless of how
# many articles are stored.
DATA_QUALITY_RULES = {
    "title_present": {"dimension": "completeness", "weight": 10},
    "publication_date_present": {"dimension": "completeness", "weight": 8},
    "source_present": {"dimension": "completeness", "weight": 5},
    "url_present": {"dimension": "completeness", "weight": 5},
    "content_sufficient": {"dimension": "completeness", "weight": 7},
    "publication_date_valid": {"dimension": "validity", "weight": 5},
    "publication_not_future": {"dimension": "validity", "weight": 5},
    "crawl_after_publication": {"dimension": "validity", "weight": 5},
    "url_valid": {"dimension": "validity", "weight": 5},
    "url_unique": {"dimension": "uniqueness", "weight": 10},
    "headline_unique": {"dimension": "uniqueness", "weight": 5},
    "content_unique": {"dimension": "uniqueness", "weight": 5},
    "source_crawl_fresh": {"dimension": "timeliness", "weight": 10},
    "crawl_delay_acceptable": {"dimension": "timeliness", "weight": 5},
    "source_domain_consistent": {"dimension": "consistency", "weight": 5},
    "category_standardized": {"dimension": "consistency", "weight": 5},
}

DATA_QUALITY_DIMENSIONS = {
    "completeness": {"label": "Kelengkapan", "weight": 35},
    "validity": {"label": "Validitas", "weight": 20},
    "uniqueness": {"label": "Keunikan", "weight": 20},
    "timeliness": {"label": "Ketepatan Waktu", "weight": 15},
    "consistency": {"label": "Konsistensi", "weight": 10},
}

MIN_ARTICLE_CONTENT_LENGTH = 200
MAX_SOURCE_CRAWL_AGE_MINUTES = 120
CRITICAL_SOURCE_CRAWL_AGE_MINUTES = 360
MAX_PUBLICATION_TO_CRAWL_HOURS = 72
ARTICLE_RETENTION_DAYS = 30

ALLOWED_ARTICLE_CATEGORIES = {
    "General",
    "Business",
    "Financial",
    "Sports",
    "International",
    "Entertainment",
    "Science",
    "Law",
    "Regional",
    "Fact Check",
}
