# DharoharGrid Backend

Three independent FastAPI services. Each is a complete, standalone app with
its own dependencies, `.env`, and process — none of them import from each
other. They share one Supabase project (`cultural_nodes` + the graph tables
below), which is what makes them agree with each other and with the
frontend's client-side fallback data.

| Service | Port (suggested) | Purpose |
|---|---|---|
| [`AI Backend`](AI%20Backend) | 8001 | RAG docent — grounded Q&A for Akashvani's ask bar |
| [`Spatial Backend`](Spatial%20Backend) | 8002 | Geofence scan — session-tracked node-trigger state for the map |
| [`Obsidian Backend`](Obsidian%20Backend) | 8003 | The discovery-graph pipeline, community-submission review, and read API for Discover |

## Quickest path: one click

Double-click **`start.bat`** at the repository root (or run `python
bootstrap.py` directly on macOS/Linux). It installs every dependency,
applies the schema if it can, builds the graph if it's empty, starts all
three servers plus the frontend, and opens your browser — safe to re-run any
time, it skips whatever's already done. See the big docstring at the top of
[`bootstrap.py`](../bootstrap.py) for exactly what each step does.

The one thing it can't do without one extra piece of config: applying
`schema.sql` needs a **direct Postgres connection string**, not just the
Supabase API key you already have in each `.env`. Until you add
`SUPABASE_DB_URL=` to `Backend/Obsidian Backend/.env` (Supabase dashboard →
Settings → Database → Connection string), that one step stays manual — see
below — and `bootstrap.py` will tell you so instead of failing silently.

## Manual setup (what the one-click script automates)

1. **Database schema** — open the Supabase SQL editor for this project and
   run [`schema.sql`](schema.sql) once. It's idempotent (safe to re-run).
   Creates/extends `cultural_nodes`, `clusters`, `node_clusters`,
   `synapse_edges`, `community_submissions` (+ its Storage bucket), and the
   `match_cultural_nodes` vector-search function.

2. **Per-service install** (repeat for each of the three folders):
   ```bash
   cd "Backend/<service folder>"
   pip install -r requirements.txt
   ```
   `.env` already exists in each folder with working credentials for this
   project — `.env.example` is the template if you ever need to point at a
   different Supabase project or LLM provider.

3. **Build the discovery graph** (Obsidian Backend owns this — it's the only
   service that writes to `cultural_nodes`/`clusters`/`synapse_edges`; AI
   Backend and Spatial Backend only ever read them):
   ```bash
   cd "Backend/Obsidian Backend"
   python -m app.pipeline.build_graph
   ```
   This is the "just add the Supabase and LLM keys" step: it seeds all 420
   nodes, AI-enriches the ones with boilerplate text, embeds everything,
   AI-prunes duplicates, builds the supercluster/subcluster taxonomy, and
   forms AI-adjudicated synapse edges. It calls the LLM a few hundred times,
   so expect it to take a while on first run — it's fully resumable
   (`--from <step>` / `--only <step>`, see the module's docstring), safe to
   re-run, and idempotent at each step.

4. **Run each service**:
   ```bash
   cd "Backend/AI Backend"        && uvicorn app.main:app --port 8001
   cd "Backend/Spatial Backend"   && uvicorn app.main:app --port 8002
   cd "Backend/Obsidian Backend"  && uvicorn app.main:app --port 8003
   ```

All three are optional from the frontend's point of view — see below.

## Community submissions & the admin dashboard

The map's **Contribute** button posts to `Obsidian Backend :8003/api/v1/
submissions` — title, lore, photo, and a location, landing in the
`community_submissions` table with `status='pending'` (photos in the
`community-photos` Storage bucket). Nothing here touches the live graph yet.

Logging in as Admin on the homepage (`Admin` / `abcd1234`) now redirects to
[`admin-dashboard.html`](../admin-dashboard.html) instead of just closing the
modal. It lists pending submissions, lets you edit the category and add/
remove tags per submission, then **Approve** or **Reject**. Approving runs
`app/pipeline/incremental.py` — the same enrich → embed → dedupe → cluster →
synapse steps `build_graph.py` runs in bulk, scoped to just that one node —
so it's categorized, connected, and checked for duplicates against the
existing graph in a few seconds instead of waiting for the next full run.

This project has no real backend auth anywhere (the admin login is a
client-side check, same as before this feature) — the submissions API and
the dashboard's session gate are both demo-grade, not something to expose
publicly without adding real auth first. Said plainly in the code too (see
`app/routers/submissions.py`'s docstring).

## Frontend integration

Every integration point is additive and fails soft: if a backend isn't
running, the page falls back to exactly what it did before this backend
existed, with a short request timeout so a dead server never hangs the UI.

- **Akashvani** (`akashvani.html`) calls `AI Backend :8001/api/v1/docent/ask`
  for real RAG answers; on any failure/timeout it falls back to the existing
  demo preview replies.
- **Discover** (`Discover/`) calls `Obsidian Backend :8003/api/v1/graph/full`
  for the real AI-built graph; on any failure it falls back to the existing
  client-side synapse engine (same one as before, unchanged).
- **Map** (`map.html`) keeps its instant client-side radar as the only thing
  the UI waits on; it additionally fires a non-blocking, best-effort call to
  `Spatial Backend :8002/api/v1/spatial/scan` alongside it purely for
  server-side session logging — nothing about the map's rendering path
  depends on that call succeeding or even completing in time. The
  Contribute form and the admin dashboard talk to the Obsidian Backend the
  same fail-soft way.

Change the port/host each page targets by editing the `API_BASE`/similar
constant near the top of that integration's script — nothing is hardcoded
deeper than one constant per page.
