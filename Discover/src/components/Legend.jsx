import { GROUP_META } from "../lib/textUtils";
import { TIER_META } from "./GraphCanvas";

export default function Legend({ tierCounts }) {
  return (
    <div className="liquid-glass absolute left-4 top-4 z-20 flex w-[min(200px,55vw)] flex-col gap-2.5 rounded-2xl border border-hairline-strong bg-white/[0.06] px-3.5 py-3 text-[10px] uppercase tracking-wide text-white/50 backdrop-blur-glass shadow-glass sm:left-6 sm:top-6">
      <div className="flex flex-col gap-1.5">
        {Object.entries(GROUP_META).map(([key, meta]) => (
          <div key={key} className="flex items-center gap-2">
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full"
              style={{ background: meta.color }}
            />
            <span>{meta.label}</span>
          </div>
        ))}
      </div>
      <div className="h-px bg-hairline" />
      <div className="flex flex-col gap-1.5">
        {Object.entries(TIER_META).map(([key, meta]) => (
          <div key={key} className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-2">
              <span
                className="inline-block h-0.5 w-3.5 shrink-0"
                style={{
                  background: meta.dash
                    ? `repeating-linear-gradient(90deg, ${meta.color} 0 2px, transparent 2px 4px)`
                    : meta.color,
                }}
              />
              {meta.label}
            </span>
            <span className="text-white/35">{tierCounts?.[key] ?? 0}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
