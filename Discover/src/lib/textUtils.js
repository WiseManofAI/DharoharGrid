// Shared text + geo helpers for the synapse engine.
//
// The raw rajasthan_master.json famous_for/docent_details fields are mostly
// auto-generated boilerplate (e.g. "This fort represents the grassroots
// cultural infrastructure of Rajasthan.") repeated near-verbatim across
// dozens of nodes. Treating that filler as a real similarity signal would
// manufacture fake "shared traits" — exactly what Master Spec §4/§5 warns
// against. So instead of naive TF-IDF over free text, we extract the small
// amount of genuinely structured fact buried in those templates (GI origin
// town, GI type, ASI-protected district) and fall back to real proper-noun
// overlap in titles. See synapseEngine.js for how these are combined.

export const STOPWORDS = new Set([
  "a","an","the","of","in","on","at","to","for","and","or","with","by",
  "is","are","was","were","this","that","these","those","its","it",
  "as","from","near",
]);

// Descriptive/type words common enough across titles that overlap on them
// alone isn't meaningful evidence of a connection (every third node title
// contains "fort" or "temple").
export const GENERIC_TITLE_WORDS = new Set([
  "fort","forts","fortress","temple","temples","monument","monuments",
  "gate","gates","palace","palaces","haveli","havelis","chhatri","chhatris",
  "ruins","memorial","memorials","museum","museums","tomb","tombs",
  "shrine","shrines","castle","castles","building","buildings","statue",
  "statues","inscriptions","old","ancient","historic","historical","house",
  "wall","walls","city","garden","gardens","well","stepwell","step",
]);

// Rajasthan's districts + a handful of well-known towns/villages that show
// up in node titles — used to detect a real shared place even when the
// ASI "located in the X district" phrasing isn't present.
export const KNOWN_PLACES = [
  "jaipur","jodhpur","udaipur","jaisalmer","bikaner","ajmer","kota",
  "bharatpur","alwar","bundi","chittorgarh","pali","sikar","nagaur",
  "dungarpur","banswara","barmer","jhunjhunu","jalore","sirohi","tonk",
  "dausa","karauli","dholpur","bhilwara","rajsamand","pratapgarh","churu",
  "hanumangarh","ganganagar","baran","jhalawar","sawai madhopur","bagru",
  "sanganer","pushkar","nathdwara","osian","ranakpur","deshnoke","kumbhalgarh",
  "mandawa","shekhawati","abu","mount abu","kuldhara","pokaran","tijara",
];

const GENERIC_ERA_VALUES = new Set([
  "local heritage","government protected antiquity","historical database",
  "historical heritage","traditional heritage","annual cultural event",
]);

export function tokenize(text) {
  if (!text) return [];
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length >= 3 && !STOPWORDS.has(t));
}

// Meaningful (non-generic) title tokens — the closest thing this dataset
// has to genuine proper-noun/keyword content.
export function meaningfulTitleTokens(title) {
  return new Set(
    tokenize(title).filter((t) => !GENERIC_TITLE_WORDS.has(t) && t.length >= 4)
  );
}

const DISTRICT_RE = /located in the ([A-Za-z\s]+?) district/i;
const ORIGIN_RE = /officially originates from ([^.]+)\./i;
const TYPE_RE = /Type:\s*([A-Z\s]+)\./;

// Real structured facts hiding inside the templated famous_for/docent_details
// strings — a lightweight stand-in for the "ingestion & structuring" LLM
// layer described in Master Spec §4 Layer 1.
export function extractAttributes(node) {
  const famousFor = node.famousFor || "";
  const docentDetails = node.docentDetails || "";
  const title = node.title || "";

  let place = null;
  const districtMatch = DISTRICT_RE.exec(famousFor);
  if (districtMatch) place = districtMatch[1].trim().toLowerCase();

  const originMatch = ORIGIN_RE.exec(docentDetails);
  if (!place && originMatch) {
    const origin = originMatch[1].trim().toLowerCase();
    const known = KNOWN_PLACES.find((p) => origin.includes(p));
    place = known || origin;
  }

  if (!place) {
    const haystack = title.toLowerCase();
    place = KNOWN_PLACES.find((p) => haystack.includes(p)) || null;
  }

  let giType = null;
  const typeMatch = TYPE_RE.exec(docentDetails);
  if (typeMatch) giType = typeMatch[1].trim().toLowerCase();

  const eraRaw = (node.era || "").trim();
  const era = eraRaw && !GENERIC_ERA_VALUES.has(eraRaw.toLowerCase()) ? eraRaw : null;

  return {
    place,
    giType,
    era,
    titleTokens: meaningfulTitleTokens(title),
  };
}

export function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

export function normalizeTitle(title) {
  return (title || "")
    .toLowerCase()
    .replace(/\(.*?\)/g, "")
    .replace(/[^a-z0-9\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function prettyCategory(cat) {
  if (!cat) return "Heritage Site";
  return cat
    .split("_")
    .map((w) => (w === "ASI" || w === "GI" ? w : w.charAt(0) + w.slice(1).toLowerCase()))
    .join(" ");
}

export const GROUP_META = {
  tangible: { label: "Tangible Heritage", color: "#e2b357" },
  intangible: { label: "Intangible Heritage", color: "#8bb2ff" },
  gastro: { label: "Gastronomy & Craft", color: "#6ee7b7" },
};
