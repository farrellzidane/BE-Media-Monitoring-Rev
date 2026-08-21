import re

from dataclasses import dataclass
from functools import lru_cache

from config.settings import NEWS_TOPIC, TOPIC_KEYWORDS


# Some crawlers collect every paragraph on the page, including recommendations
# and footer text. Restrict verification to the article lead so unrelated page
# content cannot make an article pass the topic check.
ARTICLE_LEAD_LENGTH = 3000


# These terms can describe non-cybersecurity subjects. They only count when
# repeated in a digital context or when accompanied by a stronger term.
CONTEXTUAL_CYBERSECURITY_KEYWORDS = frozenset({
    "vulnerability",
    "vulnerabilities",
    "kerentanan",
    "security risk",
    "risiko keamanan",
})


# These terms provide useful context but are not proof of cybersecurity by
# themselves. SOC and IAM are also ambiguous acronyms (system-on-chip and
# ordinary words/names), so they need stronger evidence.
SUPPORTING_ONLY_CYBERSECURITY_KEYWORDS = frozenset({
    "digital infrastructure",
    "infrastruktur digital",
    "infrastruktur teknologi informasi",
    "soc",
    "iam",
})


DIGITAL_CONTEXT_TERMS = (
    "account",
    "akun",
    "application",
    "aplikasi",
    "cloud",
    "computer",
    "cyber",
    "data",
    "database",
    "device",
    "digital",
    "email",
    "internet",
    "jaringan",
    "kata sandi",
    "komputer",
    "mobile",
    "network",
    "online",
    "password",
    "perangkat",
    "server",
    "siber",
    "sistem",
    "software",
    "system",
    "teknologi informasi",
    "web",
    "website",
)


@dataclass(frozen=True)
class TopicVerification:
    is_related: bool
    topic: str
    matched_keywords: tuple[str, ...]
    reason: str


@lru_cache(maxsize=None)
def _term_pattern(term):
    """Compile a case-insensitive whole-word/phrase pattern."""

    phrase = r"\s+".join(
        re.escape(part)
        for part in term.split()
    )

    return re.compile(
        rf"(?<!\w){phrase}(?!\w)",
        re.IGNORECASE,
    )


def _keyword_counts(text, keywords):
    return {
        keyword: len(_term_pattern(keyword).findall(text))
        for keyword in keywords
        if _term_pattern(keyword).search(text)
    }


def _format_keywords(keywords):
    return ", ".join(keywords[:5])


def verify_article_topic(article, topic=NEWS_TOPIC):
    """Return an explainable topic-verification result for an article."""

    keywords = tuple(
        keyword.lower()
        for keyword in TOPIC_KEYWORDS.get(topic, ())
    )

    if not keywords:
        return TopicVerification(
            is_related=False,
            topic=topic,
            matched_keywords=(),
            reason=f"no verification keywords are configured for {topic}",
        )

    title = str(getattr(article, "title", "") or "")
    content = str(getattr(article, "content", "") or "")
    lead = content[:ARTICLE_LEAD_LENGTH]

    title_counts = _keyword_counts(title, keywords)
    lead_counts = _keyword_counts(lead, keywords)

    matched_keywords = tuple(
        keyword
        for keyword in keywords
        if keyword in title_counts or keyword in lead_counts
    )

    if topic != "cybersecurity":
        return TopicVerification(
            is_related=bool(matched_keywords),
            topic=topic,
            matched_keywords=matched_keywords,
            reason=(
                f"matched whole-word topic terms: "
                f"{_format_keywords(matched_keywords)}"
                if matched_keywords
                else "no whole-word topic term in the title or article lead"
            ),
        )

    contextual = CONTEXTUAL_CYBERSECURITY_KEYWORDS
    supporting_only = SUPPORTING_ONLY_CYBERSECURITY_KEYWORDS
    direct = set(keywords) - contextual - supporting_only

    title_direct = tuple(
        keyword
        for keyword in keywords
        if keyword in direct and keyword in title_counts
    )
    lead_direct = tuple(
        keyword
        for keyword in keywords
        if keyword in direct and keyword in lead_counts
    )

    if title_direct:
        return TopicVerification(
            is_related=True,
            topic=topic,
            matched_keywords=matched_keywords,
            reason=(
                "verified by cybersecurity term(s) in the title: "
                f"{_format_keywords(title_direct)}"
            ),
        )

    if lead_direct:
        return TopicVerification(
            is_related=True,
            topic=topic,
            matched_keywords=matched_keywords,
            reason=(
                "verified by cybersecurity term(s) in the article lead: "
                f"{_format_keywords(lead_direct)}"
            ),
        )

    contextual_matches = tuple(
        keyword
        for keyword in keywords
        if keyword in contextual
        and (keyword in title_counts or keyword in lead_counts)
    )
    contextual_occurrences = sum(
        title_counts.get(keyword, 0) + lead_counts.get(keyword, 0)
        for keyword in contextual_matches
    )
    has_digital_context = bool(
        _keyword_counts(
            f"{title} {lead}",
            DIGITAL_CONTEXT_TERMS,
        )
    )

    if contextual_matches and has_digital_context and (
        any(keyword in title_counts for keyword in contextual_matches)
        or contextual_occurrences >= 2
    ):
        return TopicVerification(
            is_related=True,
            topic=topic,
            matched_keywords=matched_keywords,
            reason=(
                "verified by repeated/contextual cybersecurity evidence: "
                f"{_format_keywords(contextual_matches)}"
            ),
        )

    if matched_keywords:
        return TopicVerification(
            is_related=False,
            topic=topic,
            matched_keywords=matched_keywords,
            reason=(
                "only ambiguous or supporting term(s) matched: "
                f"{_format_keywords(matched_keywords)}"
            ),
        )

    return TopicVerification(
        is_related=False,
        topic=topic,
        matched_keywords=(),
        reason="no whole-word cybersecurity term in the title or article lead",
    )
