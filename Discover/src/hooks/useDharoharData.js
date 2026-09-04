import { useEffect, useState } from "react";
import { supabase, isSupabaseConfigured } from "../lib/supabaseClient";
import { mockNodes, mockEdges } from "../lib/mockData";

/**
 * Phase 2: pulls nodes (notes) and edges (linkages) from Supabase on mount.
 *
 * Expected schema (adjust table/column names to match your project, or pass
 * overrides via the `tables` option):
 *
 *   notes  — id (pk), title (text), content (text, markdown)
 *   edges  — id (pk), source (fk -> notes.id), target (fk -> notes.id),
 *            status (text: "confirmed" | "ai_discovered")
 *
 * Falls back to local mock data if Supabase env vars aren't configured yet,
 * so the graph is always inspectable.
 */
export function useDharoharData({
  notesTable = "notes",
  edgesTable = "edges",
} = {}) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [usingMockData, setUsingMockData] = useState(!isSupabaseConfigured);

  useEffect(() => {
    let cancelled = false;

    async function fetchGraphData() {
      setLoading(true);
      setError(null);

      if (!isSupabaseConfigured) {
        console.log("[DharoharGrid] Using mock nodes:", mockNodes);
        console.log("[DharoharGrid] Using mock edges:", mockEdges);
        if (!cancelled) {
          setNodes(mockNodes);
          setEdges(mockEdges);
          setUsingMockData(true);
          setLoading(false);
        }
        return;
      }

      try {
        const [notesRes, edgesRes] = await Promise.all([
          supabase.from(notesTable).select("id, title, content"),
          supabase.from(edgesTable).select("id, source, target, status"),
        ]);

        if (notesRes.error) throw notesRes.error;
        if (edgesRes.error) throw edgesRes.error;

        console.log("[DharoharGrid] Fetched nodes:", notesRes.data);
        console.log("[DharoharGrid] Fetched edges:", edgesRes.data);

        if (!cancelled) {
          setNodes(notesRes.data ?? []);
          setEdges(edgesRes.data ?? []);
          setUsingMockData(false);
          setLoading(false);
        }
      } catch (err) {
        console.error("[DharoharGrid] Failed to fetch graph data:", err);
        if (!cancelled) {
          // Degrade gracefully to mock data rather than showing an empty graph
          setNodes(mockNodes);
          setEdges(mockEdges);
          setUsingMockData(true);
          setError(err);
          setLoading(false);
        }
      }
    }

    fetchGraphData();
    return () => {
      cancelled = true;
    };
  }, [notesTable, edgesTable]);

  return { nodes, edges, loading, error, usingMockData };
}
