-- ============================================================================
-- DharoharGrid — Supabase schema (run once in the Supabase SQL editor)
-- ============================================================================
-- Idempotent: safe to re-run. Backs all three backend services:
--   AI Backend        -> reads cultural_nodes + match_cultural_nodes() RPC
--   Spatial Backend    -> reads cultural_nodes (lat/lng)
--   Obsidian Backend   -> owns/writes cultural_nodes, clusters, node_clusters,
--                         synapse_edges via its pipeline (seed/enrich/dedupe/
--                         cluster/synapse — see Backend/Obsidian Backend/app/pipeline)
-- ============================================================================

create extension if not exists vector;
create extension if not exists pgcrypto;  -- for gen_random_uuid()

-- ----------------------------------------------------------------------------
-- cultural_nodes — one row per heritage node (matches rajasthanNodes.js 1:1
-- by node_id so the frontend's client-side dataset and the backend agree)
-- ----------------------------------------------------------------------------
create table if not exists cultural_nodes (
  node_id          text primary key,
  title            text not null,
  category         text,
  heritage_group   text,                 -- tangible | intangible | gastro
  era              text,
  district         text,
  gi_type          text,                 -- handicraft | food stuff | natural goods (GI nodes only)
  latitude         double precision,
  longitude        double precision,
  famous_for       text,
  docent_details   text,
  nearby_culture   text,
  content          text,                 -- best-available description (original or ai_enriched)
  content_source   text not null default 'original',   -- original | ai_enriched
  trust_status     text not null default 'verified',   -- verified | community_contributed | ai_enriched | merged_duplicate | disputed
  merged_into      text references cultural_nodes(node_id),
  vector_embedding vector(384),          -- bge-small-en-v1.5 output size
  photo_url        text,
  source_refs      jsonb,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

-- Backfill columns individually too, in case an older cultural_nodes table
-- already exists from before this schema (e.g. the friend's original
-- single-row insert_cultural_node.py table).
alter table cultural_nodes add column if not exists category text;
alter table cultural_nodes add column if not exists heritage_group text;
alter table cultural_nodes add column if not exists era text;
alter table cultural_nodes add column if not exists district text;
alter table cultural_nodes add column if not exists gi_type text;
alter table cultural_nodes add column if not exists latitude double precision;
alter table cultural_nodes add column if not exists longitude double precision;
alter table cultural_nodes add column if not exists famous_for text;
alter table cultural_nodes add column if not exists docent_details text;
alter table cultural_nodes add column if not exists nearby_culture text;
alter table cultural_nodes add column if not exists content_source text not null default 'original';
alter table cultural_nodes add column if not exists trust_status text not null default 'verified';
alter table cultural_nodes add column if not exists merged_into text references cultural_nodes(node_id);
alter table cultural_nodes add column if not exists photo_url text;
alter table cultural_nodes add column if not exists source_refs jsonb;
alter table cultural_nodes add column if not exists created_at timestamptz not null default now();
alter table cultural_nodes add column if not exists updated_at timestamptz not null default now();

create index if not exists idx_cultural_nodes_group on cultural_nodes (heritage_group);
create index if not exists idx_cultural_nodes_district on cultural_nodes (district);
create index if not exists idx_cultural_nodes_merged on cultural_nodes (merged_into);
-- No embedding index (ivfflat/hnsw): at a few hundred rows a sequential
-- cosine scan is sub-millisecond and an index would need re-tuning as the
-- dataset grows. Add one later if the node count reaches the tens of
-- thousands.

-- ----------------------------------------------------------------------------
-- clusters — the multi-facet supercluster/subcluster taxonomy. A node can
-- belong to several clusters at once (its heritage-type, its subtype, its
-- district, its era band, its craft family) via node_clusters below.
-- ----------------------------------------------------------------------------
create table if not exists clusters (
  cluster_id  text primary key,
  name        text not null,
  kind        text not null,   -- root | heritage_type | subtype | district | era_band | craft_family
  parent_id   text references clusters(cluster_id),
  description text,
  created_at  timestamptz not null default now()
);

create index if not exists idx_clusters_kind on clusters (kind);
create index if not exists idx_clusters_parent on clusters (parent_id);

create table if not exists node_clusters (
  node_id    text not null references cultural_nodes(node_id) on delete cascade,
  cluster_id text not null references clusters(cluster_id) on delete cascade,
  primary key (node_id, cluster_id)
);

create index if not exists idx_node_clusters_cluster on node_clusters (cluster_id);

-- ----------------------------------------------------------------------------
-- synapse_edges — the AI-formed cross-links (Master Spec §5 Feature 2)
-- ----------------------------------------------------------------------------
create table if not exists synapse_edges (
  edge_id     bigserial primary key,
  source_id   text not null references cultural_nodes(node_id) on delete cascade,
  target_id   text not null references cultural_nodes(node_id) on delete cascade,
  tier        text not null,   -- verified | source_supported | potential | contradictory
  score       double precision,
  rationale   text not null,
  formed_by   text not null default 'ai_pipeline',  -- ai_pipeline | manual
  created_at  timestamptz not null default now(),
  constraint synapse_edges_ordered_pair check (source_id < target_id),
  unique (source_id, target_id)
);

create index if not exists idx_synapse_edges_source on synapse_edges (source_id);
create index if not exists idx_synapse_edges_target on synapse_edges (target_id);
create index if not exists idx_synapse_edges_tier on synapse_edges (tier);

-- ----------------------------------------------------------------------------
-- community_submissions — map "Contribute" form intake. Nothing here ever
-- touches cultural_nodes/the live graph until an admin approves it (see the
-- Obsidian Backend's app/routers/submissions.py) — this table is the holding
-- area the plan called "a separate folder", with photos in the paired
-- Storage bucket below.
-- ----------------------------------------------------------------------------
create table if not exists community_submissions (
  submission_id    uuid primary key default gen_random_uuid(),
  title            text not null,
  description      text not null,
  category         text,                 -- admin-assigned/confirmed taxonomy category
  tags             text[] not null default '{}',  -- free-form admin-editable keywords
  latitude         double precision,
  longitude        double precision,
  photo_path       text,                 -- object path inside the community-photos bucket
  contributor_name text,
  contributor_note text,
  status           text not null default 'pending',  -- pending | approved | rejected
  promoted_node_id text references cultural_nodes(node_id),
  reviewed_by      text,
  reviewed_at      timestamptz,
  created_at       timestamptz not null default now()
);

create index if not exists idx_submissions_status on community_submissions (status);

-- Storage bucket for contributed photos — provisioned via SQL (Supabase
-- exposes its bucket registry as a normal table) so schema.sql is still the
-- single source of truth for "what does a fresh project need."
insert into storage.buckets (id, name, public)
values ('community-photos', 'community-photos', true)
on conflict (id) do nothing;

-- Public read, open insert (this is a demo-grade "no real auth" project —
-- see the note in Obsidian Backend's submissions router). Tighten these
-- policies before any real deployment.
drop policy if exists "community-photos public read" on storage.objects;
create policy "community-photos public read"
  on storage.objects for select
  using (bucket_id = 'community-photos');

drop policy if exists "community-photos public upload" on storage.objects;
create policy "community-photos public upload"
  on storage.objects for insert
  with check (bucket_id = 'community-photos');

-- ----------------------------------------------------------------------------
-- match_cultural_nodes — vector similarity search RPC used by the AI Backend
-- docent endpoint (unchanged call signature from the original app.py).
-- ----------------------------------------------------------------------------
create or replace function match_cultural_nodes (
  query_embedding vector(384),
  match_count int default 3
)
returns table (
  node_id text,
  title text,
  content text,
  similarity float
)
language sql stable
as $$
  select
    cultural_nodes.node_id,
    cultural_nodes.title,
    cultural_nodes.content,
    1 - (cultural_nodes.vector_embedding <=> query_embedding) as similarity
  from cultural_nodes
  where cultural_nodes.merged_into is null
    and cultural_nodes.vector_embedding is not null
  order by cultural_nodes.vector_embedding <=> query_embedding
  limit match_count;
$$;
