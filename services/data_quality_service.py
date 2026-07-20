import re

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from urllib.parse import parse_qsl, urlencode, urlparse

from config.settings import (
    ALLOWED_ARTICLE_CATEGORIES,
    ARTICLE_RETENTION_DAYS,
    CRITICAL_SOURCE_CRAWL_AGE_MINUTES,
    DATA_QUALITY_DIMENSIONS,
    DATA_QUALITY_RULES,
    MAX_PUBLICATION_TO_CRAWL_HOURS,
    MAX_SOURCE_CRAWL_AGE_MINUTES,
    MIN_ARTICLE_CONTENT_LENGTH,
)
from repositories.article_repository import ArticleRepository, article_repository


RULE_METADATA = {
    "title_present": (
        "Judul tersedia",
        "Setiap artikel harus memiliki judul.",
        "Lengkapi judul artikel yang kosong.",
    ),
    "publication_date_present": (
        "Tanggal publikasi tersedia",
        "Setiap artikel harus memiliki tanggal publikasi.",
        "Isi tanggal publikasi dari metadata sumber.",
    ),
    "source_present": (
        "Sumber tersedia",
        "Setiap artikel harus memiliki nama sumber.",
        "Lengkapi atau petakan nama sumber artikel.",
    ),
    "url_present": (
        "URL tersedia",
        "Setiap artikel harus memiliki URL asal.",
        "Simpan URL kanonis dari artikel sumber.",
    ),
    "content_sufficient": (
        "Konten memadai",
        f"Konten artikel minimal {MIN_ARTICLE_CONTENT_LENGTH} karakter.",
        "Periksa parser konten pada artikel yang terlalu pendek.",
    ),
    "publication_date_valid": (
        "Format tanggal valid",
        "Tanggal publikasi harus dapat dibaca sebagai tanggal ISO.",
        "Normalisasi tanggal publikasi ke format YYYY-MM-DD.",
    ),
    "publication_not_future": (
        "Tanggal tidak di masa depan",
        "Tanggal publikasi tidak boleh melewati waktu saat ini.",
        "Periksa zona waktu dan parser tanggal publikasi.",
    ),
    "crawl_after_publication": (
        "Urutan tanggal logis",
        "Waktu crawl harus sama atau setelah waktu publikasi.",
        "Periksa zona waktu crawl dan tanggal artikel.",
    ),
    "url_valid": (
        "Format URL valid",
        "URL harus menggunakan HTTP/HTTPS dan memiliki hostname.",
        "Perbaiki ekstraksi atau normalisasi URL artikel.",
    ),
    "url_unique": (
        "URL unik",
        "URL kanonis tidak boleh tersimpan lebih dari sekali.",
        "Gabungkan artikel dengan URL kanonis yang sama.",
    ),
    "headline_unique": (
        "Headline unik",
        "Headline dibandingkan setelah huruf, spasi, dan tanda baca dinormalisasi.",
        "Tinjau artikel dengan headline yang sama.",
    ),
    "content_unique": (
        "Konten unik",
        "Konten identik dibandingkan setelah spasi dinormalisasi.",
        "Tinjau dan gabungkan konten identik.",
    ),
    "source_crawl_fresh": (
        "Crawl sumber tepat waktu",
        f"Setiap sumber harus dicrawl dalam {MAX_SOURCE_CRAWL_AGE_MINUTES} menit terakhir.",
        "Periksa jadwal, koneksi, dan kegagalan crawler sumber.",
    ),
    "crawl_delay_acceptable": (
        "Jeda publikasi ke crawl",
        f"Artikel sebaiknya ditemukan dalam {MAX_PUBLICATION_TO_CRAWL_HOURS} jam.",
        "Tingkatkan frekuensi atau cakupan crawler.",
    ),
    "source_domain_consistent": (
        "Domain sesuai sumber",
        "Domain URL harus konsisten dengan domain utama sumber.",
        "Periksa pemetaan sumber atau URL hasil redirect.",
    ),
    "category_standardized": (
        "Kategori terstandar",
        "Kategori harus menggunakan taksonomi yang didukung.",
        "Petakan kategori sumber ke kategori standar.",
    ),
}


def _has_value(value):
    return value is not None and str(value).strip() != ""


def _parse_datetime(value, end_of_day=False):
    if not _has_value(value):
        return None

    normalized = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed_date = date.fromisoformat(normalized)
        except ValueError:
            return None
        parsed = datetime.combine(
            parsed_date,
            time.max if end_of_day else time.min,
        )

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _normalize_text(value):
    return " ".join(str(value).casefold().split()) if _has_value(value) else ""


def _normalize_title(value):
    normalized = _normalize_text(value)
    return re.sub(r"[^\w\s]", "", normalized, flags=re.UNICODE)


def _valid_url(value):
    if not _has_value(value):
        return False
    parsed = urlparse(str(value).strip())
    try:
        parsed.port
    except ValueError:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)


def _canonical_url(value):
    if not _valid_url(value):
        return _normalize_text(value)

    parsed = urlparse(str(value).strip())
    hostname = (parsed.hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if parsed.port and not (
        parsed.scheme.lower() == "http" and parsed.port == 80
        or parsed.scheme.lower() == "https" and parsed.port == 443
    ):
        hostname = f"{hostname}:{parsed.port}"

    tracking_parameters = {"fbclid", "gclid"}
    query = urlencode(sorted(
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in tracking_parameters
    ))
    path = parsed.path.rstrip("/") or "/"
    return parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=hostname,
        path=path,
        params="",
        query=query,
        fragment="",
    ).geturl()


def _base_domain(value):
    if not _valid_url(value):
        return ""
    hostname = (urlparse(str(value).strip()).hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    parts = hostname.split(".")
    if len(parts) <= 2:
        return hostname
    country_second_levels = {"co.id", "co.uk", "com.au", "com.sg", "co.jp"}
    suffix = ".".join(parts[-2:])
    return ".".join(parts[-3:]) if suffix in country_second_levels else suffix


def _duplicate_failures(values):
    seen = set()
    failures = 0
    for value in values:
        if value in seen:
            failures += 1
        else:
            seen.add(value)
    return failures


def _score_status(score):
    if score >= 95:
        return "excellent"
    if score >= 85:
        return "healthy"
    if score >= 70:
        return "warning"
    return "critical"


def _rule_result(key, applicable, failed):
    config = DATA_QUALITY_RULES[key]
    label, description, recommendation = RULE_METADATA[key]
    passed = max(applicable - failed, 0)
    score = round((passed / applicable) * 100, 1) if applicable else 100.0
    severity = "healthy" if failed == 0 else (
        "critical" if score < 70 else "warning"
    )
    return {
        "key": key,
        "label": label,
        "description": description,
        "recommendation": recommendation,
        "dimension": config["dimension"],
        "weight": config["weight"],
        "applicable": applicable,
        "passed": passed,
        "failed": failed,
        "score": score,
        "severity": severity,
    }


def _normalize_current_time(now=None):
    current_time = now or datetime.now()
    if current_time.tzinfo is not None:
        current_time = current_time.astimezone().replace(tzinfo=None)
    return current_time


def _prepare_records(articles):
    records = [
        {
            "index": index,
            "title": article[0],
            "source": article[1],
            "category": article[2],
            "published_date": article[3],
            "crawl_date": article[4],
            "url": article[5],
            "content": article[6],
        }
        for index, article in enumerate(articles)
    ]

    for record in records:
        record["published_at"] = _parse_datetime(record["published_date"])
        record["crawl_at"] = _parse_datetime(record["crawl_date"])
        record["normalized_title"] = _normalize_title(record["title"])
        record["normalized_content"] = _normalize_text(record["content"])
        record["canonical_url"] = _canonical_url(record["url"])
        record["base_domain"] = _base_domain(record["url"])
    return records


def _build_source_context(records, current_time):
    records_by_source = defaultdict(list)
    for record in records:
        if _has_value(record["source"]):
            records_by_source[str(record["source"]).strip()].append(record)

    dominant_domain_by_source = {}
    for source, source_records in records_by_source.items():
        domains = [record["base_domain"] for record in source_records if record["base_domain"]]
        dominant_domain_by_source[source] = Counter(domains).most_common(1)[0][0] if domains else ""

    source_reports = []
    for source, source_records in sorted(records_by_source.items()):
        crawl_times = [record["crawl_at"] for record in source_records if record["crawl_at"]]
        last_crawl = max(crawl_times) if crawl_times else None
        crawl_age_minutes = (
            max(0.0, (current_time - last_crawl).total_seconds() / 60)
            if last_crawl
            else None
        )
        metadata_issues = sum(
            1
            for record in source_records
            if not all(
                _has_value(record[field])
                for field in ("title", "published_date", "url", "content")
            )
        )
        if crawl_age_minutes is None or crawl_age_minutes >= CRITICAL_SOURCE_CRAWL_AGE_MINUTES:
            status = "critical"
        elif crawl_age_minutes >= MAX_SOURCE_CRAWL_AGE_MINUTES or metadata_issues:
            status = "warning"
        else:
            status = "healthy"
        source_reports.append({
            "name": source,
            "status": status,
            "last_crawl": last_crawl.isoformat(sep=" ", timespec="seconds") if last_crawl else None,
            "crawl_age_minutes": round(crawl_age_minutes, 1) if crawl_age_minutes is not None else None,
            "articles": len(source_records),
            "issues": metadata_issues,
        })
    return records_by_source, dominant_domain_by_source, source_reports


def get_data_quality_report(
    repository: ArticleRepository = article_repository,
    now=None,
):
    current_time = _normalize_current_time(now)

    articles = repository.get_all()
    total_articles = len(articles)
    if not total_articles:
        return {
            "total_articles": 0,
            "missing_dates": 0,
            "empty_titles": 0,
            "duplicate_titles": 0,
            "old_articles": 0,
            "quality_score": 0.0,
            "status": "critical",
            "dimensions": [],
            "rules": [],
            "sources": [],
        }

    records = _prepare_records(articles)

    titles = [record["normalized_title"] for record in records if record["normalized_title"]]
    urls = [record["canonical_url"] for record in records if _has_value(record["url"])]
    contents = [record["normalized_content"] for record in records if record["normalized_content"]]

    valid_publication_records = [record for record in records if record["published_at"]]
    valid_date_pair_records = [
        record
        for record in valid_publication_records
        if record["crawl_at"]
    ]

    records_by_source, dominant_domain_by_source, source_reports = _build_source_context(
        records,
        current_time,
    )

    source_domain_candidates = [
        record
        for record in records
        if _has_value(record["source"]) and record["base_domain"]
    ]
    category_candidates = [record for record in records if _has_value(record["category"])]

    rule_inputs = {
        "title_present": (total_articles, sum(not _has_value(record["title"]) for record in records)),
        "publication_date_present": (total_articles, sum(not _has_value(record["published_date"]) for record in records)),
        "source_present": (total_articles, sum(not _has_value(record["source"]) for record in records)),
        "url_present": (total_articles, sum(not _has_value(record["url"]) for record in records)),
        "content_sufficient": (
            total_articles,
            sum(len(_normalize_text(record["content"])) < MIN_ARTICLE_CONTENT_LENGTH for record in records),
        ),
        "publication_date_valid": (
            sum(_has_value(record["published_date"]) for record in records),
            sum(_has_value(record["published_date"]) and not record["published_at"] for record in records),
        ),
        "publication_not_future": (
            len(valid_publication_records),
            sum(record["published_at"] > current_time for record in valid_publication_records),
        ),
        "crawl_after_publication": (
            len(valid_date_pair_records),
            sum(record["crawl_at"] < record["published_at"] for record in valid_date_pair_records),
        ),
        "url_valid": (
            sum(_has_value(record["url"]) for record in records),
            sum(_has_value(record["url"]) and not _valid_url(record["url"]) for record in records),
        ),
        "url_unique": (len(urls), _duplicate_failures(urls)),
        "headline_unique": (len(titles), _duplicate_failures(titles)),
        "content_unique": (len(contents), _duplicate_failures(contents)),
        "source_crawl_fresh": (
            len(source_reports),
            sum(
                source["crawl_age_minutes"] is None
                or source["crawl_age_minutes"] >= MAX_SOURCE_CRAWL_AGE_MINUTES
                for source in source_reports
            ),
        ),
        "crawl_delay_acceptable": (
            len(valid_date_pair_records),
            sum(
                record["crawl_at"] - record["published_at"]
                > timedelta(hours=MAX_PUBLICATION_TO_CRAWL_HOURS)
                for record in valid_date_pair_records
            ),
        ),
        "source_domain_consistent": (
            len(source_domain_candidates),
            sum(
                record["base_domain"]
                != dominant_domain_by_source[str(record["source"]).strip()]
                for record in source_domain_candidates
            ),
        ),
        "category_standardized": (
            len(category_candidates),
            sum(record["category"] not in ALLOWED_ARTICLE_CATEGORIES for record in category_candidates),
        ),
    }

    rules = [
        _rule_result(key, *rule_inputs[key])
        for key in DATA_QUALITY_RULES
    ]
    quality_score = round(
        sum(rule["score"] * rule["weight"] for rule in rules) / 100,
        1,
    )

    dimensions = []
    for key, config in DATA_QUALITY_DIMENSIONS.items():
        dimension_rules = [rule for rule in rules if rule["dimension"] == key]
        rule_weight = sum(rule["weight"] for rule in dimension_rules)
        score = round(
            sum(rule["score"] * rule["weight"] for rule in dimension_rules) / rule_weight,
            1,
        )
        dimensions.append({
            "key": key,
            "label": config["label"],
            "weight": config["weight"],
            "score": score,
            "weighted_score": round(score * config["weight"] / 100, 1),
            "issues": sum(rule["failed"] for rule in dimension_rules),
            "status": _score_status(score),
        })

    published_dates = [record["published_at"] for record in records if record["published_at"]]
    retention_cutoff = current_time - timedelta(days=ARTICLE_RETENTION_DAYS)

    return {
        "total_articles": total_articles,
        # Backwards-compatible summary fields for older consumers.
        "missing_dates": rule_inputs["publication_date_present"][1],
        "empty_titles": rule_inputs["title_present"][1],
        "duplicate_titles": rule_inputs["headline_unique"][1],
        "old_articles": sum(published_at < retention_cutoff for published_at in published_dates),
        "quality_score": quality_score,
        "status": _score_status(quality_score),
        "dimensions": dimensions,
        "rules": rules,
        "sources": source_reports,
    }


def _article_evidence(record, passed, observed_value, expected_value, reason):
    return {
        "id": f"article-{record['index'] + 1}",
        "entity_type": "article",
        "result": "passed" if passed else "failed",
        "title": str(record["title"]).strip() if _has_value(record["title"]) else "Tanpa judul",
        "source": str(record["source"]).strip() if _has_value(record["source"]) else "Tidak diketahui",
        "url": str(record["url"]).strip() if _has_value(record["url"]) else None,
        "published_date": record["published_date"],
        "crawl_date": record["crawl_date"],
        "observed_value": observed_value,
        "expected_value": expected_value,
        "reason": reason,
    }


def _source_evidence(source, passed):
    age = source["crawl_age_minutes"]
    observed = "Belum pernah dicrawl" if age is None else f"{age:.1f} menit sejak crawl terakhir"
    return {
        "id": f"source-{source['name']}",
        "entity_type": "source",
        "result": "passed" if passed else "failed",
        "title": source["name"],
        "source": source["name"],
        "url": None,
        "published_date": None,
        "crawl_date": source["last_crawl"],
        "observed_value": observed,
        "expected_value": f"Kurang dari {MAX_SOURCE_CRAWL_AGE_MINUTES} menit",
        "reason": (
            "Crawl sumber masih berada dalam batas waktu."
            if passed
            else "Crawl sumber melewati batas waktu yang ditetapkan."
        ),
    }


def _unique_evidence(records, value_key, expected_value, value_label):
    evidence = []
    first_by_value = {}
    for record in records:
        value = record[value_key]
        if not value:
            continue
        duplicate_of = first_by_value.get(value)
        passed = duplicate_of is None
        if passed:
            first_by_value[value] = record
        observed = value if len(value) <= 180 else f"{value[:177]}..."
        reason = (
            f"{value_label} belum pernah muncul pada data sebelumnya."
            if passed
            else f"Sama dengan artikel: {duplicate_of['title'] or 'Tanpa judul'}."
        )
        evidence.append(_article_evidence(
            record,
            passed,
            observed,
            expected_value,
            reason,
        ))
    return evidence


def _build_rule_evidence(
    rule_key,
    records,
    source_reports,
    dominant_domain_by_source,
    current_time,
):
    evidence = []

    field_rules = {
        "title_present": ("title", "Judul tidak kosong", "judul"),
        "publication_date_present": ("published_date", "Tanggal publikasi tidak kosong", "tanggal publikasi"),
        "source_present": ("source", "Nama sumber tidak kosong", "sumber"),
        "url_present": ("url", "URL asal tidak kosong", "URL"),
    }
    if rule_key in field_rules:
        field, expected, label = field_rules[rule_key]
        for record in records:
            passed = _has_value(record[field])
            observed = str(record[field]).strip() if passed else "Kosong"
            evidence.append(_article_evidence(
                record,
                passed,
                observed,
                expected,
                f"{label.capitalize()} tersedia." if passed else f"{label.capitalize()} belum tersedia.",
            ))
        return evidence

    if rule_key == "content_sufficient":
        for record in records:
            length = len(record["normalized_content"])
            passed = length >= MIN_ARTICLE_CONTENT_LENGTH
            evidence.append(_article_evidence(
                record,
                passed,
                f"{length} karakter",
                f"Minimal {MIN_ARTICLE_CONTENT_LENGTH} karakter",
                "Panjang konten memadai." if passed else "Konten terlalu pendek atau kosong.",
            ))
        return evidence

    if rule_key == "publication_date_valid":
        for record in records:
            if not _has_value(record["published_date"]):
                continue
            passed = record["published_at"] is not None
            evidence.append(_article_evidence(
                record,
                passed,
                str(record["published_date"]),
                "Tanggal ISO yang dapat dibaca",
                "Format tanggal valid." if passed else "Format tanggal tidak dapat dibaca.",
            ))
        return evidence

    if rule_key == "publication_not_future":
        for record in records:
            if not record["published_at"]:
                continue
            passed = record["published_at"] <= current_time
            evidence.append(_article_evidence(
                record,
                passed,
                str(record["published_date"]),
                f"Tidak melewati {current_time.isoformat(sep=' ', timespec='seconds')}",
                "Tanggal publikasi tidak berada di masa depan." if passed else "Tanggal publikasi berada di masa depan.",
            ))
        return evidence

    if rule_key in {"crawl_after_publication", "crawl_delay_acceptable"}:
        for record in records:
            if not record["published_at"] or not record["crawl_at"]:
                continue
            delay_hours = (record["crawl_at"] - record["published_at"]).total_seconds() / 3600
            if rule_key == "crawl_after_publication":
                passed = delay_hours >= 0
                expected = "Waktu crawl ≥ waktu publikasi"
                reason = "Urutan waktu logis." if passed else "Waktu crawl mendahului waktu publikasi."
            else:
                passed = delay_hours <= MAX_PUBLICATION_TO_CRAWL_HOURS
                expected = f"Jeda maksimal {MAX_PUBLICATION_TO_CRAWL_HOURS} jam"
                reason = "Jeda crawl masih dapat diterima." if passed else "Artikel ditemukan terlalu lambat."
            evidence.append(_article_evidence(
                record,
                passed,
                f"Jeda {delay_hours:.1f} jam",
                expected,
                reason,
            ))
        return evidence

    if rule_key == "url_valid":
        for record in records:
            if not _has_value(record["url"]):
                continue
            passed = _valid_url(record["url"])
            evidence.append(_article_evidence(
                record,
                passed,
                str(record["url"]),
                "URL HTTP/HTTPS dengan hostname valid",
                "Format URL valid." if passed else "Skema, hostname, atau port URL tidak valid.",
            ))
        return evidence

    if rule_key == "url_unique":
        return _unique_evidence(
            [record for record in records if _has_value(record["url"])],
            "canonical_url",
            "URL kanonis hanya muncul satu kali",
            "URL kanonis",
        )

    if rule_key == "headline_unique":
        return _unique_evidence(
            [record for record in records if record["normalized_title"]],
            "normalized_title",
            "Headline ternormalisasi hanya muncul satu kali",
            "Headline ternormalisasi",
        )

    if rule_key == "content_unique":
        return _unique_evidence(
            [record for record in records if record["normalized_content"]],
            "normalized_content",
            "Konten ternormalisasi hanya muncul satu kali",
            "Konten ternormalisasi",
        )

    if rule_key == "source_crawl_fresh":
        return [
            _source_evidence(
                source,
                source["crawl_age_minutes"] is not None
                and source["crawl_age_minutes"] < MAX_SOURCE_CRAWL_AGE_MINUTES,
            )
            for source in source_reports
        ]

    if rule_key == "source_domain_consistent":
        for record in records:
            if not _has_value(record["source"]) or not record["base_domain"]:
                continue
            source = str(record["source"]).strip()
            expected_domain = dominant_domain_by_source[source]
            passed = record["base_domain"] == expected_domain
            evidence.append(_article_evidence(
                record,
                passed,
                record["base_domain"],
                expected_domain,
                "Domain sesuai sumber." if passed else "Domain berbeda dari domain utama sumber.",
            ))
        return evidence

    if rule_key == "category_standardized":
        expected_categories = ", ".join(sorted(ALLOWED_ARTICLE_CATEGORIES))
        for record in records:
            if not _has_value(record["category"]):
                continue
            passed = record["category"] in ALLOWED_ARTICLE_CATEGORIES
            evidence.append(_article_evidence(
                record,
                passed,
                str(record["category"]),
                expected_categories,
                "Kategori terdaftar pada taksonomi." if passed else "Kategori belum dipetakan ke taksonomi standar.",
            ))
        return evidence

    raise ValueError(f"Unknown data-quality rule: {rule_key}")


def get_data_quality_rule_evidence(
    rule_key,
    result_filter="all",
    limit=25,
    offset=0,
    repository: ArticleRepository = article_repository,
    now=None,
):
    if rule_key not in DATA_QUALITY_RULES:
        raise ValueError(f"Unknown data-quality rule: {rule_key}")
    if result_filter not in {"all", "passed", "failed"}:
        raise ValueError(f"Unknown evidence result filter: {result_filter}")

    current_time = _normalize_current_time(now)
    articles = repository.get_all()
    records = _prepare_records(articles)
    _, dominant_domain_by_source, source_reports = _build_source_context(
        records,
        current_time,
    )
    evidence = _build_rule_evidence(
        rule_key,
        records,
        source_reports,
        dominant_domain_by_source,
        current_time,
    )
    rule = _rule_result(
        rule_key,
        len(evidence),
        sum(item["result"] == "failed" for item in evidence),
    )
    dimension = DATA_QUALITY_DIMENSIONS[rule["dimension"]]
    filtered_evidence = (
        evidence
        if result_filter == "all"
        else [item for item in evidence if item["result"] == result_filter]
    )

    return {
        "rule": {**rule, "dimension_label": dimension["label"]},
        "result_filter": result_filter,
        "total": len(evidence),
        "filtered_total": len(filtered_evidence),
        "limit": limit,
        "offset": offset,
        "evidence": filtered_evidence[offset:offset + limit],
    }
