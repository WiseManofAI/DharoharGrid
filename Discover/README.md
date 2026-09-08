# DharoharGrid — Discover (standalone app)

A standalone React + Vite + Tailwind app implementing the Obsidian-style
"Discovery Graph Engine" from the DharoharGrid site's **Discover** button.
Covers all four build phases:

1. **UI shell** — glassmorphic `DharoharGrid` container, back button, floating
   search box. (`src/App.jsx`, `src/components/`)
2. **Supabase integration** — fetches nodes (`notes` table) and edges
   (`edges` table, with a `confirmed` / `ai_discovered` status) on mount.
   (`src/lib/supabaseClient.js`, `src/hooks/useDharoharData.js`)
3. **Force-directed graph** — `react-force-graph-2d`, degree-based node
   sizing, red edges for unconfirmed AI linkages, white for confirmed,
   violet hover highlight that fades everything else, search-to-pan.
   (`src/components/GraphCanvas.jsx`)
4. **Markdown node view** — clicking a node swaps the glass tab from graph to
   a `react-markdown` rendered text view; Back returns to the graph first,
   then to the parent site. (`src/components/NodeDetailView.jsx`)

## Running it

```bash
npm install
npm run dev
```

The app runs immediately with **mock data** (`src/lib/mockData.js`) — eight
sample Rajasthan heritage nodes — so the whole UI is clickable before
Supabase is wired up.

## Connecting Supabase

1. Copy `.env.example` to `.env` and fill in your project URL + anon key.
2. Create two tables (or point the hook at your existing ones — see below):

   ```sql
   create table notes (
     id text primary key,
     title text not null,
     content text -- markdown
   );

   create table edges (
     id text primary key,
     source text references notes(id),
     target text references notes(id),
     status text check (status in ('confirmed', 'ai_discovered'))
   );
   ```

3. If your table/column names differ, pass overrides:
   `useDharoharData({ notesTable: "your_notes", edgesTable: "your_edges" })`
   in `src/App.jsx`. Column names (`id`, `title`, `content`, `source`,
   `target`, `status`) are currently expected as-is — adjust the `.select()`
   calls in `src/hooks/useDharoharData.js` if yours differ.

## Wiring up the "Discover" button

In the main site's `index.html`, the button is:

```html
<button class="dynamic-explore-btn dynamic-discover-btn">
  <span class="btn-text">Discover</span>
  <span class="btn-glow-layer"></span>
</button>
```

It currently has no handler. Two ways to connect it, depending on how you
deploy this app:

**A. Separate deployment (simplest)** — point it at wherever this app is
hosted:

```html
<script>
  document.querySelector(".dynamic-discover-btn").addEventListener("click", () => {
    window.location.href = "https://your-dharoharGrid-app-url/";
  });
</script>
```

**B. Same SPA / router** — if you fold `index.html`'s content into the React
app as a route instead, just `navigate("/discover")` on click and drop the
`window.location.href` fallback in `src/App.jsx`'s `handleBack` in favor of
your router's back navigation.

The `PARENT_SITE_URL` constant at the top of `src/App.jsx` controls where
the in-app **Back** button sends the user once they're already at the graph
(as opposed to the text view, where Back first returns to the graph).
