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

from crawler.tribun import (
    get_article as get_tribun_article,
    get_latest_article_urls as get_tribun_urls
)

from crawler.liputan6 import (
    get_article as get_liputan6_article,
    get_latest_article_urls as get_liputan6_urls
)

from crawler.kumparan import (
    get_article as get_kumparan_article,
    get_latest_article_urls as get_kumparan_urls
)

from crawler.okezone import (
    get_article as get_okezone_article,
    get_latest_article_urls as get_okezone_urls
)

from crawler.sindonews import (
    get_article as get_sindonews_article,
    get_latest_article_urls as get_sindonews_urls
)


SOURCES = [
    ("CNN", get_cnn_urls, get_cnn_article),
    ("Detik", get_detik_urls, get_detik_article),
    ("Kompas", get_kompas_urls, get_kompas_article),
    ("Tempo", get_tempo_urls, get_tempo_article),
    ("CNBC", get_cnbc_urls, get_cnbc_article),
    ("Tribunnews", get_tribun_urls, get_tribun_article),
    ("Liputan6", get_liputan6_urls, get_liputan6_article),
    ("Kumparan", get_kumparan_urls, get_kumparan_article),
    ("Okezone", get_okezone_urls, get_okezone_article),
    ("Sindonews", get_sindonews_urls, get_sindonews_article),
]