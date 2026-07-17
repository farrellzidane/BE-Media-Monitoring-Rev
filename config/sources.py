from crawler.cnn import (
    get_article as get_cnn_article,
    get_latest_article_urls as get_cnn_urls
)

from crawler.detik import (
    get_article as get_detik_article,
    get_latest_article_urls as get_detik_urls
)

from crawler.kompas import (
    get_article as get_kompas_article,
    get_latest_article_urls as get_kompas_urls
)

from crawler.tempo import (
    get_article as get_tempo_article,
    get_latest_article_urls as get_tempo_urls
)

from crawler.cnbc import (
    get_article as get_cnbc_article,
    get_latest_article_urls as get_cnbc_urls
)


SOURCES = [
    ("CNN", get_cnn_urls, get_cnn_article),
    ("Detik", get_detik_urls, get_detik_article),
    ("Kompas", get_kompas_urls, get_kompas_article),
    ("Tempo", get_tempo_urls, get_tempo_article),
    ("CNBC", get_cnbc_urls, get_cnbc_article),
]