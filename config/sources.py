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

from crawler.generic import build_source


INTERNATIONAL_SOURCES = [
    ("The Hacker News", "https://thehackernews.com/", ("https://feeds.feedburner.com/TheHackersNews",)),
    ("SecurityWeek", "https://www.securityweek.com/", ("https://feeds.feedburner.com/securityweek",)),
    ("Cybersecurity News", "https://cybersecuritynews.com/", ("https://cybersecuritynews.com/feed/",)),
    ("Cybersecurity Dive", "https://www.cybersecuritydive.com/", ("https://www.cybersecuritydive.com/feeds/news/",)),
    ("BleepingComputer", "https://www.bleepingcomputer.com/", ("https://www.bleepingcomputer.com/feed/",)),
    ("Dark Reading", "https://www.darkreading.com/", ("https://www.darkreading.com/rss.xml",)),
    ("KrebsOnSecurity", "https://krebsonsecurity.com/", ("https://krebsonsecurity.com/feed/",)),
    ("The Record", "https://therecord.media/", ("https://therecord.media/feed",)),
    ("Help Net Security", "https://www.helpnetsecurity.com/", ("https://www.helpnetsecurity.com/feed/",)),
    ("Infosecurity Magazine", "https://www.infosecurity-magazine.com/", ("https://www.infosecurity-magazine.com/rss/news/",)),
]

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


def get_sources():
    configured = list(INTERNATIONAL_SOURCES)
    try:
        from services.settings_service import get_custom_sources
        configured.extend(get_custom_sources())
    except RuntimeError:
        pass

    sources = list(SOURCES)
    seen_urls = set()
    for source_config in configured:
        source_name, source_url, *feed_config = source_config
        feed_urls = feed_config[0] if feed_config else ()
        if source_url in seen_urls:
            continue
        seen_urls.add(source_url)
        get_urls, get_article = build_source(source_name, source_url, feed_urls)
        sources.append((source_name, get_urls, get_article))
    return sources