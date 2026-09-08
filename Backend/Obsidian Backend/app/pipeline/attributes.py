"""Structured-fact extraction from the raw node text.

Python port of the frontend's Discover/src/lib/textUtils.js extractAttributes
— kept in sync deliberately so the backend's district/gi_type/group logic
matches what the client-side fallback graph already does. The reasoning for
why this exists at all (rather than naive TF-IDF over free text) is the same:
famous_for/docent_details are mostly auto-generated boilerplate ("This fort
represents the grassroots cultural infrastructure of Rajasthan."), so we pull
out the few genuinely structured facts hiding in them instead of treating the
filler as a similarity signal.
"""
import re

KNOWN_PLACES = [
    "jaipur", "jodhpur", "udaipur", "jaisalmer", "bikaner", "ajmer", "kota",
    "bharatpur", "alwar", "bundi", "chittorgarh", "pali", "sikar", "nagaur",
    "dungarpur", "banswara", "barmer", "jhunjhunu", "jalore", "sirohi", "tonk",
    "dausa", "karauli", "dholpur", "bhilwara", "rajsamand", "pratapgarh", "churu",
    "hanumangarh", "ganganagar", "baran", "jhalawar", "sawai madhopur", "bagru",
    "sanganer", "pushkar", "nathdwara", "osian", "ranakpur", "deshnoke",
    "kumbhalgarh", "mandawa", "shekhawati", "abu", "mount abu", "kuldhara",
    "pokaran", "tijara",
]

GENERIC_TITLE_WORDS = {
    "fort", "forts", "fortress", "temple", "temples", "monument", "monuments",
    "gate", "gates", "palace", "palaces", "haveli", "havelis", "chhatri",
    "chhatris", "ruins", "memorial", "memorials", "museum", "museums", "tomb",
    "tombs", "shrine", "shrines", "castle", "castles", "building", "buildings",
    "statue", "statues", "inscriptions", "old", "ancient", "historic",
    "historical", "house", "wall", "walls", "city", "garden", "gardens",
    "well", "stepwell", "step",
}

STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or",
    "with", "by", "is", "are", "was", "were", "this", "that", "these",
    "those", "its", "it", "as", "from", "near",
}

DISTRICT_RE = re.compile(r"located in the ([A-Za-z\s]+?) district", re.I)
ORIGIN_RE = re.compile(r"officially originates from ([^.]+)\.", re.I)
TYPE_RE = re.compile(r"Type:\s*([A-Z\s]+)\.")

GENERIC_ERA_VALUES = {
    "local heritage", "government protected antiquity", "historical database",
    "historical heritage", "traditional heritage", "annual cultural event",
}


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    cleaned = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return [t for t in cleaned.split() if len(t) >= 3 and t not in STOPWORDS]


def meaningful_title_tokens(title: str) -> set[str]:
    return {
        t for t in tokenize(title)
        if t not in GENERIC_TITLE_WORDS and len(t) >= 4
    }


def extract_place(title: str, famous_for: str, docent_details: str) -> str | None:
    m = DISTRICT_RE.search(famous_for or "")
    if m:
        return m.group(1).strip().lower()

    m = ORIGIN_RE.search(docent_details or "")
    if m:
        origin = m.group(1).strip().lower()
        for p in KNOWN_PLACES:
            if p in origin:
                return p
        return origin

    haystack = (title or "").lower()
    for p in KNOWN_PLACES:
        if p in haystack:
            return p
    return None


def extract_gi_type(docent_details: str) -> str | None:
    m = TYPE_RE.search(docent_details or "")
    return m.group(1).strip().lower() if m else None


def extract_era(era_raw: str) -> str | None:
    era = (era_raw or "").strip()
    if era and era.lower() not in GENERIC_ERA_VALUES:
        return era
    return None


BOILERPLATE_PATTERNS = [
    re.compile(r"^A local .+ documented by open-source ground mapping\.$", re.I),
    re.compile(r"^A prominent (architectural|cultural) landmark", re.I),
    re.compile(r"^A centrally protected monument located in the .+ district\.$", re.I),
    re.compile(r"represents the grassroots cultural infrastructure of Rajasthan\.?$", re.I),
    re.compile(r"stands as an important (node|monument)", re.I),
    re.compile(r"^A legally protected Geographical Indication", re.I),
    re.compile(r"^Registered under the Geographical Indications of Goods Act\.", re.I),
]


def is_boilerplate(famous_for: str, docent_details: str) -> bool:
    """True if either field is (near-)verbatim auto-generated filler text
    rather than a genuine, distinguishing description."""
    for field in (famous_for or "", docent_details or ""):
        for pattern in BOILERPLATE_PATTERNS:
            if pattern.search(field):
                return True
    # Also flag suspiciously short descriptions with no real content.
    combined = f"{famous_for or ''} {docent_details or ''}".strip()
    return len(combined) < 40


def normalize_title(title: str) -> str:
    t = (title or "").lower()
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"[^a-z0-9\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def group_for_category(category: str) -> str:
    if not category:
        return "tangible"
    c = category.upper()
    if c.startswith("INTANGIBLE"):
        return "intangible"
    if c.startswith("GASTRONOMY"):
        return "gastro"
    return "tangible"


def pretty_category(category: str) -> str:
    if not category:
        return "Heritage Site"
    parts = category.split("_")
    words = [p if p in ("ASI", "GI") else p.capitalize() for p in parts]
    return " ".join(words)
