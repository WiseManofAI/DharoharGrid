// Mirrors Backend/Obsidian Backend/app/pipeline/taxonomy.py's SUBTYPE_RULES /
// HERITAGE_TYPE_CLUSTERS — kept in sync deliberately so the graph clusters
// the same way whether it's using the real backend-computed taxonomy or the
// client-side fallback (see useDharoharData.js).

export const HERITAGE_TYPE_CLUSTERS = {
  tangible: { id: "heritage-tangible", name: "Tangible Heritage" },
  intangible: { id: "heritage-intangible", name: "Intangible Heritage" },
  gastro: { id: "heritage-gastro", name: "Gastronomy & Craft" },
};

const SUBTYPE_RULES = {
  TANGIBLE_FORT: ["subtype-forts-castles", "Forts & Castles"],
  TANGIBLE_CASTLE: ["subtype-forts-castles", "Forts & Castles"],
  TANGIBLE_ASI_PROTECTED: ["subtype-asi-protected", "ASI Protected Monuments"],
  TANGIBLE_CITY_GATE: ["subtype-city-gates", "City Gates & Walls"],
  TANGIBLE_STEPWELL: ["subtype-stepwells", "Stepwells & Water Architecture"],
  TANGIBLE_TOMB: ["subtype-tombs-memorials", "Tombs & Memorials"],
  TANGIBLE_MEMORIAL: ["subtype-tombs-memorials", "Tombs & Memorials"],
  TANGIBLE_ARCHAEOLOGICAL_SITE: ["subtype-archaeological", "Archaeological Sites & Ruins"],
  TANGIBLE_RUINS: ["subtype-archaeological", "Archaeological Sites & Ruins"],
  TANGIBLE_MANOR: ["subtype-manors-havelis", "Manors & Havelis"],
  TANGIBLE_WAYSIDE_SHRINE: ["subtype-shrines-temples", "Shrines & Temples"],
  TANGIBLE_CANNON: ["subtype-military-relics", "Military & Colonial Relics"],
  TANGIBLE_AIRCRAFT: ["subtype-military-relics", "Military & Colonial Relics"],
  TANGIBLE_BOMB_CRATER: ["subtype-military-relics", "Military & Colonial Relics"],
  TANGIBLE_HERITAGE: ["subtype-general-monuments", "General Monuments"],
  TANGIBLE_MONUMENT: ["subtype-general-monuments", "General Monuments"],
  TANGIBLE_BUILDING: ["subtype-general-monuments", "General Monuments"],
  TANGIBLE_YES: ["subtype-general-monuments", "General Monuments"],
  TANGIBLE_FOR: ["subtype-general-monuments", "General Monuments"],
  INTANGIBLE_FESTIVAL: ["subtype-festivals", "Festivals"],
  INTANGIBLE_MUSIC: ["subtype-music", "Music Traditions"],
  INTANGIBLE_DANCE: ["subtype-dance", "Dance Traditions"],
  INTANGIBLE_CRAFT: ["subtype-craft-traditions", "Craft Traditions"],
  GASTRONOMY_OR_CRAFT_GI_TAG: ["subtype-gi-tagged", "GI-Tagged Handicrafts & Foods"],
  GASTRONOMY_HERITAGE: ["subtype-food-heritage", "Food Heritage"],
  GASTRONOMY_FESTIVAL: ["subtype-food-festivals", "Food Festivals"],
};
const SUBTYPE_FALLBACK = ["subtype-general-monuments", "General Monuments"];

export function subtypeFor(category) {
  const [id, name] = SUBTYPE_RULES[category] || SUBTYPE_FALLBACK;
  return { id, name };
}
