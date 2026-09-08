import ReactMarkdown from "react-markdown";
import { TIER_META } from "./GraphCanvas";

export default function NodeDetailView({ node, edges = [], nodesById, onJump }) {
  if (!node) return null;

  const grouped = { verified: [], source_supported: [], potential: [] };
  edges.forEach((e) => {
    const otherId = e.source === node.id ? e.target : e.source;
    const other = nodesById?.get(otherId);
    if (!other) return;
    grouped[e.tier]?.push({ ...e, other });
  });

  return (
    <div className="thin-scroll h-full w-full overflow-y-auto px-6 py-8 sm:px-10 sm:py-10">
      <article className="prose-invert mx-auto max-w-2xl text-left leading-relaxed text-white/85 [&_a]:text-gold [&_code]:rounded [&_code]:bg-white/10 [&_code]:px-1 [&_code]:py-0.5 [&_h1]:mb-4 [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:text-white [&_h2]:mt-6 [&_h2]:mb-2 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-white [&_p]:mb-3 [&_strong]:text-white/70">
        <ReactMarkdown>{node.content ?? "*No content found for this node.*"}</ReactMarkdown>

        {edges.length > 0 && (
          <div className="mt-8 border-t border-hairline pt-6">
            <h2 className="mb-1 text-lg font-semibold text-white">
              Synapse Connections &amp; Research Leads
            </h2>
            <p className="mb-4 text-xs text-white/40">
              Auto-surfaced from shared documented attributes — not asserted history. See each
              tier's confidence below.
            </p>

            {(["verified", "source_supported", "potential"]).map((tier) =>
              grouped[tier].length ? (
                <div key={tier} className="mb-4">
                  <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide" style={{ color: TIER_META[tier].color }}>
                    <span
                      className="inline-block h-1.5 w-1.5 rounded-full"
                      style={{ background: TIER_META[tier].color }}
                    />
                    {TIER_META[tier].label}
                  </div>
                  <ul className="flex flex-col gap-2">
                    {grouped[tier].map((e) => (
                      <li key={e.id}>
                        <button
                          type="button"
                          onClick={() => onJump?.(e.other.id)}
                          className="liquid-glass group w-full rounded-xl border border-hairline bg-white/[0.03] px-4 py-3 text-left transition-colors hover:border-hairline-strong hover:bg-white/[0.06]"
                        >
                          <span className="block text-sm font-medium text-white group-hover:text-gold">
                            {e.other.title}
                          </span>
                          <span className="mt-1 block text-xs leading-snug text-white/45">
                            {e.rationale}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null
            )}
          </div>
        )}
      </article>
    </div>
  );
}
