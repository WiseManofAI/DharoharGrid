import { useEffect, useMemo, useState } from "react";
import { RAJASTHAN_NODES } from "../lib/rajasthanNodes";
import { buildSynapseGraph } from "../lib/synapseEngine";
import { subtypeFor } from "../lib/clusterTaxonomy";

// Obsidian Backend (see Backend/Obsidian Backend) — serves the real,
// precomputed discovery graph: real embeddings, AI-adjudicated synapse
// edges, AI-driven dedup, and the full supercluster/subcluster taxonomy.
const OBSIDIAN_BACKEND_URL = "http://localhost:8003";
const GRAPH_FETCH_TIMEOUT_MS = 4000;

function subtypeClusterFor(node, clustersById, nodeClusterIds) {
  for (const clusterId of nodeClusterIds) {
    const cluster = clustersById.get(clusterId);
    if (cluster?.kind === "subtype") {
      return { id: cluster.cluster_id, name: cluster.name };
    }
  }
  // Backend data didn't carry a subtype membership for this node (shouldn't
  // happen once the pipeline has run, but keep the graph rendering anyway).
  return subtypeFor(node.category);
}

/** Transforms the backend's /api/v1/graph/full payload into the
 * {id, title, group, content, subtypeClusterId, ...} node shape and
 * {id, source, target, tier, rationale} edge shape the graph UI expects —
 * the same shape buildSynapseGraph() produces, so GraphCanvas/NodeDetailView
 * don't need to know which source the data came from. */
function transformBackendGraph(payload) {
  const clustersById = new Map((payload.clusters || []).map((c) => [c.cluster_id, c]));
  const clusterIdsByNode = new Map();
  (payload.node_clusters || []).forEach(({ node_id, cluster_id }) => {
    if (!clusterIdsByNode.has(node_id)) clusterIdsByNode.set(node_id, []);
    clusterIdsByNode.get(node_id).push(cluster_id);
  });

  const nodes = (payload.nodes || []).map((n) => {
    const subtype = subtypeClusterFor(n, clustersById, clusterIdsByNode.get(n.node_id) || []);
    return {
      id: n.node_id,
      title: n.title,
      category: n.category,
      group: n.heritage_group,
      era: n.era,
      lat: n.latitude,
      lng: n.longitude,
      trust: n.trust_status,
      place: n.district,
      content: n.content,
      contentSource: n.content_source,
      photo: n.photo_url,
      subtypeClusterId: subtype.id,
      subtypeClusterName: subtype.name,
    };
  });

  const edges = (payload.edges || []).map((e) => ({
    id: `edge-${e.edge_id}`,
    source: e.source_id,
    target: e.target_id,
    tier: e.tier,
    score: e.score,
    rationale: e.rationale,
  }));

  return { nodes, edges, clusters: payload.clusters || [] };
}

async function fetchBackendGraph() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), GRAPH_FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(`${OBSIDIAN_BACKEND_URL}/api/v1/graph/full`, {
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`graph backend status ${res.status}`);
    const payload = await res.json();
    return transformBackendGraph(payload);
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Loads the Discovery Graph. Tries the real Obsidian Backend first (a few
 * seconds' timeout); on any failure — not running, empty, slow — falls back
 * to computing the same shape of graph entirely client-side from the bundled
 * dataset (synapseEngine.js), so Discover is always fully functional with
 * zero backend dependency, just with a lighter-weight connection engine.
 */
export function useDharoharData() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingLiveBackend, setUsingLiveBackend] = useState(false);

  const clientSideGraph = useMemo(() => buildSynapseGraph(RAJASTHAN_NODES), []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const graph = await fetchBackendGraph();
        if (cancelled) return;
        if (!graph.nodes.length) throw new Error("graph backend returned no nodes");
        setNodes(graph.nodes);
        setEdges(graph.edges);
        setUsingLiveBackend(true);
      } catch (err) {
        if (cancelled) return;
        setNodes(clientSideGraph.nodes);
        setEdges(clientSideGraph.edges);
        setUsingLiveBackend(false);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [clientSideGraph]);

  return { nodes, edges, loading, usingLiveBackend, usingMockData: !usingLiveBackend };
}
