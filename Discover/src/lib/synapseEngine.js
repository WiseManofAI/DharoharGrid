// The DharoharGrid "Synapse" / Discovery Graph engine (Master Spec §5,
// Feature 2 — "Obsidian-Style Discovery Graph / Research Leads").
//
// This is the offline-first fallback: the real thing now runs server-side
// in Backend/Obsidian Backend — real embeddings, AI-adjudicated edges,
// AI-driven dedup, and the full supercluster/subcluster taxonomy, all
// precomputed and served from Supabase (see useDharoharData.js, which tries
// that backend first and only falls back to this module if it's
// unreachable). This module approximates the same idea entirely client-side
// with structured-attribute matching (see textUtils.extractAttributes)
// rather than naive TF-IDF, because the demo dataset's free text is
// templated boilerplate — matching on it directly would fabricate
// connections instead of surfacing real ones. Good enough to keep Discover
// fully functional with zero backend dependency.
//
// Every edge carries a confidence tier straight from the spec's trust model:
//   verified          🟢 same documented subject (duplicate archival record)
//   source_supported  🔵 grounded in a real extracted fact (shared GI origin
//                         town, shared ASI district, shared specific era)
//   potential         🟡 thematically adjacent only — surfaced as a research
//                         lead, never as an asserted historical relationship
// `contradictory` (🔴) is part of the trust model but nothing in this
// dataset currently conflicts, so no edges of that tier are generated.
import { extractAttributes, haversineKm, normalizeTitle, prettyCategory } from "./textUtils";
import { subtypeFor } from "./clusterTaxonomy";

const TOP_K_PER_NODE = 4;
const TITLE_OVERLAP_MAX_KM = 60;
const WEAK_GEO_MAX_KM = 15;

function scoreForTier(tier, extra = 0) {
  switch (tier) {
    case "verified":
      return 1;
    case "source_supported":
      return 0.8 + extra;
    case "potential_craft":
      return 0.55;
    case "potential_title":
      return Math.min(0.35 + extra * 0.05, 0.55);
    case "potential_geo":
      return extra; // pre-computed small value
    default:
      return 0;
  }
}

function rationaleFor(tier, ctx) {
  switch (tier) {
    case "verified":
      return "Duplicate archival record of the same documented subject.";
    case "source_supported_place":
      return `Both officially registered/protected under "${ctx.place}" — a shared, sourced administrative fact.`;
    case "source_supported_era":
      return `Both dated to the same documented era — "${ctx.era}".`;
    case "potential_craft":
      return `Same craft/produce classification ("${ctx.giType}") from a different town — a possible cross-regional technique lineage. Not established as historically linked by current sources; flagged as a research lead.`;
    case "potential_title":
      return `Share the keyword${ctx.words.length > 1 ? "s" : ""} "${ctx.words.join(", ")}" in their titles. A direct relationship is not established by current sources; flagged as a research lead.`;
    case "potential_geo":
      return `Both ${ctx.group} heritage nodes ${ctx.distKm.toFixed(1)} km apart with no documented link yet — proximity-only research lead.`;
    default:
      return "";
  }
}

export function buildSynapseGraph(rawNodes, options = {}) {
  const topK = options.topK ?? TOP_K_PER_NODE;

  const prepped = rawNodes.map((n) => ({
    ...n,
    attrs: extractAttributes(n),
    normTitle: normalizeTitle(n.title),
  }));

  const candidates = new Map(prepped.map((n) => [n.id, []]));

  function addCandidate(a, b, tier, score, rationale) {
    candidates.get(a.id).push({ targetId: b.id, tier, score, rationale });
    candidates.get(b.id).push({ targetId: a.id, tier, score, rationale });
  }

  for (let i = 0; i < prepped.length; i++) {
    const a = prepped[i];
    for (let j = i + 1; j < prepped.length; j++) {
      const b = prepped[j];

      // 1. Verified — same subject, duplicate record.
      if (a.normTitle && a.normTitle === b.normTitle) {
        addCandidate(a, b, "verified", scoreForTier("verified"), rationaleFor("verified"));
        continue;
      }

      const distKm = haversineKm(a.lat, a.lng, b.lat, b.lng);

      // 2. Source-supported — grounded in a real extracted fact.
      if (a.attrs.place && a.attrs.place === b.attrs.place && distKm <= 120) {
        const rationale = rationaleFor("source_supported_place", { place: a.attrs.place });
        addCandidate(a, b, "source_supported", scoreForTier("source_supported", 0.1), rationale);
        continue;
      }
      if (a.attrs.era && a.attrs.era === b.attrs.era) {
        const rationale = rationaleFor("source_supported_era", { era: a.attrs.era });
        addCandidate(a, b, "source_supported", scoreForTier("source_supported", 0.05), rationale);
        continue;
      }

      // 3. Potential — cross-region craft family (same GI type, different place).
      if (a.attrs.giType && a.attrs.giType === b.attrs.giType && a.attrs.place !== b.attrs.place) {
        const rationale = rationaleFor("potential_craft", { giType: a.attrs.giType });
        addCandidate(a, b, "potential", scoreForTier("potential_craft"), rationale);
        continue;
      }

      // 4. Potential — shared meaningful title keyword within a plausible range.
      if (distKm <= TITLE_OVERLAP_MAX_KM) {
        const shared = [...a.attrs.titleTokens].filter((t) => b.attrs.titleTokens.has(t));
        if (shared.length > 0) {
          const rationale = rationaleFor("potential_title", { words: shared.slice(0, 3) });
          addCandidate(a, b, "potential", scoreForTier("potential_title", shared.length), rationale);
          continue;
        }
      }

      // 5. Potential — weak proximity-only lead, same top-level group, very close.
      if (a.group === b.group && distKm <= WEAK_GEO_MAX_KM) {
        const geoScore = Math.max(0.12, 0.26 - (distKm / WEAK_GEO_MAX_KM) * 0.14);
        const rationale = rationaleFor("potential_geo", { group: a.group, distKm });
        addCandidate(a, b, "potential", scoreForTier("potential_geo", geoScore), rationale);
      }
    }
  }

  const edgesMap = new Map();
  candidates.forEach((list, id) => {
    list.sort((x, y) => y.score - x.score);
    list.slice(0, topK).forEach((c) => {
      const key = id < c.targetId ? `${id}|${c.targetId}` : `${c.targetId}|${id}`;
      const existing = edgesMap.get(key);
      if (!existing || c.score > existing.score) {
        edgesMap.set(key, {
          id: key,
          source: id < c.targetId ? id : c.targetId,
          target: id < c.targetId ? c.targetId : id,
          tier: c.tier,
          score: c.score,
          rationale: c.rationale,
        });
      }
    });
  });

  const nodesWithContent = prepped.map((n) => {
    const subtype = subtypeFor(n.category);
    return {
      id: n.id,
      title: n.title,
      category: n.category,
      group: n.group,
      era: n.era,
      lat: n.lat,
      lng: n.lng,
      trust: n.trust,
      place: n.attrs.place,
      content: buildContent(n),
      subtypeClusterId: subtype.id,
      subtypeClusterName: subtype.name,
    };
  });

  return { nodes: nodesWithContent, edges: Array.from(edgesMap.values()) };
}

function buildContent(n) {
  const lines = [`# ${n.title}`, ""];
  lines.push(`**Category:** ${prettyCategory(n.category)}  `);
  if (n.era) lines.push(`**Era:** ${n.era}  `);
  if (n.attrs.place) lines.push(`**Region:** ${titleCase(n.attrs.place)}  `);
  lines.push(`**Trust status:** ${n.trust || "verified"}  `);
  lines.push("");
  if (n.famousFor) lines.push(n.famousFor);
  if (n.docentDetails && n.docentDetails !== n.famousFor) lines.push("\n" + n.docentDetails);
  if (n.nearbyCulture) lines.push(`\n**Nearby culture:** ${n.nearbyCulture}`);
  return lines.join("\n");
}

function titleCase(s) {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}
