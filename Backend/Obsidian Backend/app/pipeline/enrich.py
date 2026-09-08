"""Step 2: AI content enrichment for nodes whose description is boilerplate.

Master Spec §4 Layer 1 ("Ingestion & Structuring") calls for turning raw,
thin source text into something a docent can actually narrate from. Roughly
three-quarters of this dataset's famous_for/docent_details fields are
auto-generated filler ("This fort represents the grassroots cultural
infrastructure of Rajasthan.") — this step asks the LLM to rewrite those into
a genuine 2-4 sentence description, but explicitly grounded ONLY in the
structured facts already on the row (title, category, era, district, GI
info, nearby culture). The prompt forbids inventing dates, rulers, or events
not given — this is enrichment/rephrasing, not fabrication, and every
enriched row is tagged content_source='ai_enriched' so nothing pretends to be
more verified than it is (Master Spec §5's trust-model honesty rule).

Nulls out vector_embedding on any row it touches, so embed.py (step 3)
re-embeds the improved text.
"""
from ..clients import LLMError, get_supabase, LLMClient
from . import attributes

FETCH_PAGE_SIZE = 200

SYSTEM_PROMPT = (
    "You are a careful museum cataloguer improving thin database records for "
    "a cultural heritage archive. You will be given structured facts about a "
    "single site or tradition. Write a 2-4 sentence description in a "
    "documentary, factual tone.\n\n"
    "STRICT RULES:\n"
    "- Use ONLY the facts given to you. Do not invent dates, rulers, "
    "founders, events, or historical claims that are not in the input.\n"
    "- You MAY rephrase, contextualize, and connect the given facts into "
    "readable prose (e.g. 'a fort in the X district, protected as a "
    "centrally listed monument' from separate category/district facts).\n"
    "- If the input is too thin to say anything beyond the category and "
    "location, it is fine to keep the description short and generic — do "
    "not pad with invented specifics.\n"
    "- Reply with a JSON object: {\"description\": \"...\"}"
)


def _build_user_prompt(node: dict) -> str:
    lines = [f"Title: {node['title']}", f"Category: {attributes.pretty_category(node.get('category'))}"]
    if node.get("era"):
        lines.append(f"Era: {node['era']}")
    if node.get("district"):
        lines.append(f"District/region: {node['district']}")
    if node.get("gi_type"):
        lines.append(f"GI type: {node['gi_type']}")
    if node.get("nearby_culture"):
        lines.append(f"Nearby culture note: {node['nearby_culture']}")
    if node.get("famous_for") and not attributes.is_boilerplate(node["famous_for"], ""):
        lines.append(f"Existing note: {node['famous_for']}")
    return "\n".join(lines)


def find_candidates(sb) -> list[dict]:
    candidates: list[dict] = []
    offset = 0
    while True:
        page = (
            sb.table("cultural_nodes")
            .select("node_id, title, category, era, district, gi_type, nearby_culture, famous_for, docent_details, content_source")
            .is_("merged_into", "null")
            .neq("content_source", "ai_enriched")
            .range(offset, offset + FETCH_PAGE_SIZE - 1)
            .execute()
            .data
        )
        if not page:
            break
        for row in page:
            if attributes.is_boilerplate(row.get("famous_for") or "", row.get("docent_details") or ""):
                candidates.append(row)
        offset += FETCH_PAGE_SIZE
    return candidates


def run(limit: int | None = None) -> int:
    sb = get_supabase()
    candidates = find_candidates(sb)
    if limit:
        candidates = candidates[:limit]

    print(f"[enrich] {len(candidates)} node(s) have boilerplate content and need rewriting.")
    if not candidates:
        return 0

    llm = LLMClient()
    enriched = 0
    for node in candidates:
        try:
            result = llm.chat_json(SYSTEM_PROMPT, _build_user_prompt(node))
            description = (result or {}).get("description", "").strip()
        except LLMError as e:
            print(f"[enrich] SKIP {node['node_id']}: {e}")
            continue

        if not description:
            print(f"[enrich] SKIP {node['node_id']}: empty response")
            continue

        sb.table("cultural_nodes").update(
            {
                "content": description,
                "content_source": "ai_enriched",
                "vector_embedding": None,  # force re-embed with the new text
            }
        ).eq("node_id", node["node_id"]).execute()
        enriched += 1
        print(f"[enrich] {enriched}/{len(candidates)} — {node['title']}")

    return enriched


if __name__ == "__main__":
    run()
