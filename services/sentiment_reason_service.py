import re

from functools import lru_cache


ARTICLE_LEAD_LENGTH = 3000


# Cybersecurity-impact cues mirroring the labeling criteria in
# ml/datasets/auto_labeler.py (patched/blocked/arrested = beneficial,
# breach/hacked/exploited = harmful), applied deterministically here so
# every saved article gets a short rationale without an LLM call.
POSITIVE_IMPACT_KEYWORDS = (
    "ditambal", "tambal keamanan", "patch keamanan", "berhasil dicegah",
    "berhasil digagalkan", "berhasil diblokir", "berhasil menangkal",
    "ditangkap", "dibekuk", "dibongkar", "diamankan", "diringkus",
    "audit keamanan", "lolos audit", "meningkatkan keamanan",
    "memperkuat keamanan", "penguatan keamanan", "berhasil dipulihkan",
    "pemulihan data", "diselamatkan", "pengungkapan bertanggung jawab",
    "kesadaran keamanan", "investasi keamanan", "melindungi privasi",
    "meningkatkan privasi", "perlindungan data diperkuat",
    "sertifikasi keamanan",
)

NEGATIVE_IMPACT_KEYWORDS = (
    "kebocoran data", "data bocor", "bocor data", "diretas", "peretasan",
    "dibobol", "membobol", "ransomware", "malware", "phishing",
    "serangan ddos", "dieksploitasi", "eksploitasi", "belum ditambal",
    "belum diperbaiki", "dicuri", "pencurian data", "disusupi", "kerugian",
    "lumpuh", "dijual di forum", "penipuan", "pencurian identitas",
    "gagal melindungi", "kelalaian keamanan", "terekspos",
    "data terekspos", "celah keamanan", "kerentanan kritis",
    "korban serangan", "diserang",
)


@lru_cache(maxsize=None)
def _pattern(term):
    phrase = r"\s+".join(re.escape(part) for part in term.split())
    return re.compile(rf"(?<!\w){phrase}(?!\w)", re.IGNORECASE)


def _matched_terms(text, keywords):
    return [keyword for keyword in keywords if _pattern(keyword).search(text)]


def generate_sentiment_reason(title, content, label):
    """Return a short, human-readable rationale for a sentiment label by
    surfacing the cybersecurity-impact cues found in the article's title
    and lead content."""

    haystack = f"{title or ''} {(content or '')[:ARTICLE_LEAD_LENGTH]}"

    positive_hits = _matched_terms(haystack, POSITIVE_IMPACT_KEYWORDS)
    negative_hits = _matched_terms(haystack, NEGATIVE_IMPACT_KEYWORDS)

    if label == "Positive":
        if positive_hits:
            return (
                "Dinilai positif karena artikel menyebutkan perkembangan "
                f"yang menguntungkan keamanan siber: {', '.join(positive_hits[:4])}."
            )
        return (
            "Dinilai positif berdasarkan keseluruhan konteks pemberitaan, "
            "meski tidak ada frasa dampak positif yang eksplisit terdeteksi."
        )

    if label == "Negative":
        if negative_hits:
            return (
                "Dinilai negatif karena artikel menyebutkan indikasi dampak "
                f"buruk terhadap keamanan siber: {', '.join(negative_hits[:4])}."
            )
        return (
            "Dinilai negatif berdasarkan keseluruhan konteks pemberitaan, "
            "meski tidak ada frasa dampak negatif yang eksplisit terdeteksi."
        )

    if positive_hits and negative_hits:
        return (
            "Dinilai netral karena artikel memuat indikasi campuran tanpa "
            f"dampak yang dominan: sisi positif ({', '.join(positive_hits[:2])}) "
            f"dan sisi negatif ({', '.join(negative_hits[:2])})."
        )

    return (
        "Dinilai netral karena tidak ditemukan indikasi dampak positif "
        "maupun negatif yang dominan terhadap keamanan siber; artikel "
        "bersifat informatif atau deskriptif."
    )
