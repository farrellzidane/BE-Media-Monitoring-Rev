from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# ============================================================
# NEWS TOPIC
# ============================================================

NEWS_TOPIC = "cybersecurity"

TOPIC_KEYWORDS = {
    "cybersecurity": [
        # ====================================================
        # GENERAL CYBERSECURITY
        # ====================================================
        "cybersecurity",
        "cyber security",
        "cyber attack",
        "cyberattack",
        "cyber crime",
        "cybercrime",
        "cyber threat",
        "cyber threats",
        "cyber incident",
        "cybersecurity incident",
        "cyber risk",
        "cyber defense",
        "cyber defence",
        "cyber protection",

        # ====================================================
        # INDONESIAN
        # ====================================================
        "keamanan siber",
        "keamanan cyber",
        "serangan siber",
        "serangan cyber",
        "kejahatan siber",
        "kejahatan cyber",
        "ancaman siber",
        "ancaman cyber",
        "insiden siber",
        "insiden cyber",
        "serangan digital",
        "pertahanan siber",
        "pertahanan cyber",
        "perlindungan siber",
        "perlindungan cyber",
        "risiko siber",
        "risiko cyber",

        # ====================================================
        # CYBER ATTACKS / MALWARE
        # ====================================================
        "ransomware",
        "malware",
        "spyware",
        "trojan",
        "botnet",
        "ddos",
        "denial of service",
        "distributed denial of service",
        "phishing",
        "spear phishing",
        "smishing",
        "vishing",
        "social engineering",
        "credential theft",
        "credential stealing",
        "identity theft",
        "password attack",
        "brute force",
        "brute-force",
        "account takeover",
        "cyber extortion",
        "cyber espionage",

        # ====================================================
        # VULNERABILITIES / EXPLOITS
        # ====================================================
        "vulnerability",
        "vulnerabilities",
        "kerentanan",
        "security flaw",
        "security flaws",
        "security vulnerability",
        "zero day",
        "zero-day",
        "zero day vulnerability",
        "zero-day vulnerability",
        "exploit",
        "exploitation",
        "remote code execution",
        "rce",
        "privilege escalation",
        "command injection",
        "sql injection",
        "cross site scripting",
        "xss",
        "buffer overflow",
        "security patch",
        "patch keamanan",

        # ====================================================
        # DATA SECURITY / DATA BREACH
        # ====================================================
        "data breach",
        "data breaches",
        "data leak",
        "data leakage",
        "kebocoran data",
        "pencurian data",
        "database breach",
        "stolen data",
        "exposed data",
        "data exposure",
        "data theft",
        "data security",
        "keamanan data",
        "perlindungan data",

        # ====================================================
        # HACKING
        # ====================================================
        "hacker",
        "hackers",
        "hacking",
        "hacked",
        "diretas",
        "meretas",
        "peretasan",
        "dibobol",
        "membobol",
        "membobol sistem",
        "cybercriminal",
        "cybercriminals",
        "cyber criminal",
        "cyber criminals",
        "pelaku peretasan",
        "kelompok hacker",

        # ====================================================
        # SECURITY TECHNOLOGY
        # ====================================================
        "firewall",
        "endpoint security",
        "endpoint protection",
        "antivirus",
        "anti-virus",
        "security operation center",
        "security operations center",
        "soc",
        "siem",
        "zero trust",
        "multi factor authentication",
        "multifactor authentication",
        "multi-factor authentication",
        "mfa",
        "two factor authentication",
        "two-factor authentication",
        "2fa",
        "encryption",
        "enkripsi",
        "decryption",
        "identity access management",
        "iam",
        "access control",
        "security monitoring",
        "threat detection",
        "intrusion detection",
        "intrusion prevention",

        # ====================================================
        # SECURITY ORGANIZATIONS / EXPERTS
        # ====================================================
        "badan siber dan sandi negara",
        "bssn",
        "cybersecurity agency",
        "security researcher",
        "security researchers",
        "peneliti keamanan",
        "cybersecurity researcher",
        "cybersecurity researchers",
        "incident response",
        "cyber incident response",
        "digital forensics",
        "forensik digital",

        # ====================================================
        # DIGITAL INFRASTRUCTURE SECURITY
        # ====================================================
        "critical infrastructure",
        "infrastruktur kritis",
        "digital infrastructure",
        "infrastruktur digital",
        "cloud security",
        "network security",
        "application security",
        "web security",
        "mobile security",
        "information security",
        "keamanan informasi",
        "database security",
        "server security",
        "network protection",
        "infrastruktur teknologi informasi",

        # ====================================================
        # SECURITY INCIDENT / RISK
        # ====================================================
        "security update",
        "security advisory",
        "security breach",
        "security incident",
        "security risk",
        "risiko keamanan",
        "security threat",
        "threat intelligence",
        "cyber threat intelligence",
        "incident response",
        "security alert",
        "peringatan keamanan",
        "security warning",
        "security investigation",
        "investigasi keamanan",

        # ====================================================
        # COMMON CYBERSECURITY TERMS
        # ====================================================
        "cybersecurity firm",
        "cybersecurity company",
        "cybersecurity industry",
        "cybersecurity sector",
        "cyber security firm",
        "cyber security company",
        "security software",
        "security platform",
        "security system",
        "sistem keamanan siber",
        "sistem keamanan digital",
    ]
}


# ============================================================
# NEWS SOURCES
# ============================================================

CNN_URLS = [
    "https://www.cnnindonesia.com/teknologi"
]

DETIK_URLS = [
    "https://inet.detik.com"
]

KOMPAS_URL = "https://tekno.kompas.com"

TEMPO_URL = "https://www.tempo.co/teknologi"

CNBC_URLS = [
    "https://www.cnbcindonesia.com/tech",
    "https://www.cnbcindonesia.com/news",
]

LIPUTAN6_URL = "https://www.liputan6.com/tekno"

KUMPARAN_URL = "https://kumparan.com"

OKEZONE_URLS = [
    "https://techno.okezone.com"
]

SINDONEWS_URLS = [
    "https://tekno.sindonews.com"
]

TRIBUN_URLS = [
    "https://www.tribunnews.com/techno"
]

KUMPARAN_GRAPHQL_URL = (
    "https://cdn-graphql-v4.kumparan.com/query"
)


# ============================================================
# CRAWLER SETTINGS
# ============================================================

MAX_ARTICLES = 100

REQUEST_TIMEOUT = 20

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)


# ============================================================
# OUTPUT
# ============================================================

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


# ============================================================
# DATA QUALITY
# ============================================================

DATA_QUALITY_RULES = {
    "title_present": {
        "dimension": "completeness",
        "weight": 10
    },

    "publication_date_present": {
        "dimension": "completeness",
        "weight": 8
    },

    "source_present": {
        "dimension": "completeness",
        "weight": 5
    },

    "url_present": {
        "dimension": "completeness",
        "weight": 5
    },

    "content_sufficient": {
        "dimension": "completeness",
        "weight": 7
    },

    "publication_date_valid": {
        "dimension": "validity",
        "weight": 5
    },

    "publication_not_future": {
        "dimension": "validity",
        "weight": 5
    },

    "crawl_after_publication": {
        "dimension": "validity",
        "weight": 5
    },

    "url_valid": {
        "dimension": "validity",
        "weight": 5
    },

    "url_unique": {
        "dimension": "uniqueness",
        "weight": 10
    },

    "headline_unique": {
        "dimension": "uniqueness",
        "weight": 5
    },

    "content_unique": {
        "dimension": "uniqueness",
        "weight": 5
    },

    "source_crawl_fresh": {
        "dimension": "timeliness",
        "weight": 10
    },

    "crawl_delay_acceptable": {
        "dimension": "timeliness",
        "weight": 5
    },

    "source_domain_consistent": {
        "dimension": "consistency",
        "weight": 5
    },

    "category_standardized": {
        "dimension": "consistency",
        "weight": 5
    },
}


DATA_QUALITY_DIMENSIONS = {
    "completeness": {
        "label": "Kelengkapan",
        "weight": 35
    },

    "validity": {
        "label": "Validitas",
        "weight": 20
    },

    "uniqueness": {
        "label": "Keunikan",
        "weight": 20
    },

    "timeliness": {
        "label": "Ketepatan Waktu",
        "weight": 15
    },

    "consistency": {
        "label": "Konsistensi",
        "weight": 10
    },
}


# ============================================================
# ARTICLE QUALITY / RETENTION
# ============================================================

MIN_ARTICLE_CONTENT_LENGTH = 200

MAX_SOURCE_CRAWL_AGE_MINUTES = 120

CRITICAL_SOURCE_CRAWL_AGE_MINUTES = 360

MAX_PUBLICATION_TO_CRAWL_HOURS = 72

ARTICLE_RETENTION_DAYS = 30


# ============================================================
# ARTICLE CATEGORIES
# ============================================================

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