"""The supercluster/subcluster taxonomy.

Five facets, all derived from real data (not hardcoded per-node):
  root            -- single "Rajasthan" root every node belongs to
  heritage_type   -- tangible / intangible / gastro (3 superclusters)
  subtype         -- fine-grained grouping of the raw ASI/GI category taxonomy
  district        -- one cluster per real district/town extracted from the text
  era_band        -- century-scale grouping of the era field
  craft_family    -- technique/craft lineage, for craft- and GI-relevant nodes

A node belongs to several of these facets simultaneously (root + heritage_type
+ subtype + era_band always; district and craft_family when the data supports
one). See pipeline/cluster.py for how membership is actually assigned.
"""
import re

ROOT_CLUSTER = ("root-rajasthan", "Rajasthan", "root", None, "Every DharoharGrid node — the top of the graph.")

HERITAGE_TYPE_CLUSTERS = {
    "tangible": ("heritage-tangible", "Tangible Heritage", "Physical monuments, architecture, and archaeological sites."),
    "intangible": ("heritage-intangible", "Intangible Heritage", "Performing arts, festivals, and living traditions."),
    "gastro": ("heritage-gastro", "Gastronomy & Craft", "GI-tagged foods, crafts, and culinary heritage."),
}

# raw category -> (cluster_id, cluster_name)
SUBTYPE_RULES = {
    "TANGIBLE_FORT": ("subtype-forts-castles", "Forts & Castles"),
    "TANGIBLE_CASTLE": ("subtype-forts-castles", "Forts & Castles"),
    "TANGIBLE_ASI_PROTECTED": ("subtype-asi-protected", "ASI Protected Monuments"),
    "TANGIBLE_CITY_GATE": ("subtype-city-gates", "City Gates & Walls"),
    "TANGIBLE_STEPWELL": ("subtype-stepwells", "Stepwells & Water Architecture"),
    "TANGIBLE_TOMB": ("subtype-tombs-memorials", "Tombs & Memorials"),
    "TANGIBLE_MEMORIAL": ("subtype-tombs-memorials", "Tombs & Memorials"),
    "TANGIBLE_ARCHAEOLOGICAL_SITE": ("subtype-archaeological", "Archaeological Sites & Ruins"),
    "TANGIBLE_RUINS": ("subtype-archaeological", "Archaeological Sites & Ruins"),
    "TANGIBLE_MANOR": ("subtype-manors-havelis", "Manors & Havelis"),
    "TANGIBLE_WAYSIDE_SHRINE": ("subtype-shrines-temples", "Shrines & Temples"),
    "TANGIBLE_CANNON": ("subtype-military-relics", "Military & Colonial Relics"),
    "TANGIBLE_AIRCRAFT": ("subtype-military-relics", "Military & Colonial Relics"),
    "TANGIBLE_BOMB_CRATER": ("subtype-military-relics", "Military & Colonial Relics"),
    "TANGIBLE_HERITAGE": ("subtype-general-monuments", "General Monuments"),
    "TANGIBLE_MONUMENT": ("subtype-general-monuments", "General Monuments"),
    "TANGIBLE_BUILDING": ("subtype-general-monuments", "General Monuments"),
    "TANGIBLE_YES": ("subtype-general-monuments", "General Monuments"),
    "TANGIBLE_FOR": ("subtype-general-monuments", "General Monuments"),
    "INTANGIBLE_FESTIVAL": ("subtype-festivals", "Festivals"),
    "INTANGIBLE_MUSIC": ("subtype-music", "Music Traditions"),
    "INTANGIBLE_DANCE": ("subtype-dance", "Dance Traditions"),
    "INTANGIBLE_CRAFT": ("subtype-craft-traditions", "Craft Traditions"),
    "GASTRONOMY_OR_CRAFT_GI_TAG": ("subtype-gi-tagged", "GI-Tagged Handicrafts & Foods"),
    "GASTRONOMY_HERITAGE": ("subtype-food-heritage", "Food Heritage"),
    "GASTRONOMY_FESTIVAL": ("subtype-food-festivals", "Food Festivals"),
}
SUBTYPE_FALLBACK = ("subtype-general-monuments", "General Monuments")

# Craft/technique family — matched by substring against the lowercased title.
# Order matters: first match wins, so put more specific keywords first.
CRAFT_FAMILY_RULES = [
    ("craft-block-printing", "Block Printing Family", ["block printing", "hand block", "sanganeri", "bagru"]),
    ("craft-pottery", "Pottery & Ceramics", ["pottery", "clay work", "ceramic", "blue pottery"]),
    ("craft-puppetry", "Puppetry & String Arts", ["puppet", "kathputli"]),
    ("craft-textile-weave", "Textile & Weaving Family", ["doria", "phulkari", "weav", "textile", "print"]),
    ("craft-metal-enamel", "Metalwork & Enamel", ["thewa", "enamel", "metal work"]),
    ("craft-stone-carving", "Stone & Marble Carving", ["marble", "stone carving", "sculpture", "makrana"]),
    ("craft-painting-mural", "Painting & Mural Traditions", ["painting", "mural", "art work"]),
    ("craft-food-sweets", "Food & Confectionery Heritage", ["bhujia", "mehndi", "sangri", "sweet", "cuisine", "food"]),
]


def craft_family_for(title: str) -> tuple[str, str] | None:
    haystack = (title or "").lower()
    for cluster_id, name, keywords in CRAFT_FAMILY_RULES:
        if any(kw in haystack for kw in keywords):
            return cluster_id, name
    return None


CENTURY_RE = re.compile(r"(\d{1,2})(?:st|nd|rd|th)\s+century", re.I)

ERA_BANDS = [
    ("era-ancient", "Ancient Era (pre-7th century)"),
    ("era-early-medieval", "Early Medieval Era (7th–14th century)"),
    ("era-rajput-mughal", "Rajput & Mughal Era (15th–18th century)"),
    ("era-colonial", "Colonial Era (19th century)"),
    ("era-modern", "Modern Era (20th century–present)"),
]
ERA_UNDATED = ("era-undated", "Undated Traditional Heritage")


def era_band_for(era: str | None) -> tuple[str, str]:
    if not era:
        return ERA_UNDATED
    if re.search(r"\bancient\b", era, re.I):
        return ERA_BANDS[0]

    m = CENTURY_RE.search(era)
    if not m:
        return ERA_UNDATED

    century = int(m.group(1))
    if century <= 6:
        return ERA_BANDS[0]
    if century <= 14:
        return ERA_BANDS[1]
    if century <= 18:
        return ERA_BANDS[2]
    if century == 19:
        return ERA_BANDS[3]
    return ERA_BANDS[4]


def district_cluster_for(district: str) -> tuple[str, str]:
    slug = re.sub(r"[^a-z0-9]+", "-", district.lower()).strip("-")
    return f"district-{slug}", district.title()


def subtype_for(category: str) -> tuple[str, str]:
    return SUBTYPE_RULES.get(category, SUBTYPE_FALLBACK)
