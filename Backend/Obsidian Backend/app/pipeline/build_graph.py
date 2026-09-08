"""Orchestrates the full pipeline in dependency order.

    python -m app.pipeline.build_graph                # full run
    python -m app.pipeline.build_graph --from cluster  # resume from a step
    python -m app.pipeline.build_graph --only synapse  # just one step

Every step is individually idempotent/resumable (see each module's
docstring), so re-running the whole thing after an interruption is always
safe — already-done work is detected and skipped rather than redone.
"""
import argparse
import time

from . import cluster, dedupe, embed, enrich, seed, synapse

STEPS = [
    ("seed", seed.run),
    ("enrich", enrich.run),
    ("embed", embed.run),
    ("dedupe", dedupe.run),
    ("cluster", cluster.run),
    ("synapse", synapse.run),
]
STEP_NAMES = [name for name, _ in STEPS]


def run(start_from: str | None = None, only: str | None = None):
    if only:
        selected = [(n, f) for n, f in STEPS if n == only]
    elif start_from:
        idx = STEP_NAMES.index(start_from)
        selected = STEPS[idx:]
    else:
        selected = STEPS

    print(f"[build_graph] running steps: {[n for n, _ in selected]}\n")

    for name, fn in selected:
        print(f"\n{'=' * 70}\n[build_graph] STEP: {name}\n{'=' * 70}")
        t0 = time.time()
        try:
            fn()
        except Exception as e:  # noqa: BLE001 — a failed step should not
            # silently corrupt state; surface it and stop so the operator
            # can fix (e.g. missing schema.sql) and resume with --from.
            print(f"[build_graph] STEP '{name}' FAILED after {time.time() - t0:.1f}s: {e}")
            raise
        print(f"[build_graph] step '{name}' done in {time.time() - t0:.1f}s")

    print("\n[build_graph] pipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the DharoharGrid discovery graph.")
    parser.add_argument("--from", dest="start_from", choices=STEP_NAMES, default=None)
    parser.add_argument("--only", dest="only", choices=STEP_NAMES, default=None)
    args = parser.parse_args()
    run(start_from=args.start_from, only=args.only)
