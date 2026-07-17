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
