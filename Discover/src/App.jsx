import { useMemo, useRef, useState } from "react";
import Header from "./components/Header";
import BackButton from "./components/BackButton";
import SearchBar from "./components/SearchBar";
import GraphCanvas from "./components/GraphCanvas";
import NodeDetailView from "./components/NodeDetailView";
import MatrixBackground from "./components/MatrixBackground";
import Legend from "./components/Legend";
import { useDharoharData } from "./hooks/useDharoharData";

// Where the "Back" button returns to — the parent DharoharGrid site.
// This app is built to Discover/dist/ and linked to from the root
// index.html's Discover button, so it's two directories up from there.
const PARENT_SITE_URL = "../../index.html";

export default function App() {
  const { nodes, edges, loading, usingLiveBackend } = useDharoharData();
  const [view, setView] = useState("graph"); // "graph" | "text"
  const [activeNodeId, setActiveNodeId] = useState(null);
  const graphRef = useRef(null);

  const nodesById = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);
  const activeNode = activeNodeId ? nodesById.get(activeNodeId) ?? null : null;

  const edgesByNode = useMemo(() => {
    const map = new Map();
    nodes.forEach((n) => map.set(n.id, []));
    edges.forEach((e) => {
      map.get(e.source)?.push(e);
      map.get(e.target)?.push(e);
    });
    return map;
  }, [nodes, edges]);

  const tierCounts = useMemo(() => {
    const counts = { verified: 0, source_supported: 0, potential: 0 };
    edges.forEach((e) => {
      if (counts[e.tier] !== undefined) counts[e.tier] += 1;
    });
    return counts;
  }, [edges]);

  function openNode(nodeId) {
    setActiveNodeId(nodeId);
    setView("text");
  }

  function handleSearch(query) {
    graphRef.current?.focusNode(query);
  }

  function handleBack() {
    if (view === "text") {
      setView("graph");
      setActiveNodeId(null);
      return;
    }
    window.location.href = PARENT_SITE_URL;
  }

  return (
    <div className="relative flex min-h-screen w-full flex-col items-center bg-void px-4 pb-10 sm:px-8">
      <MatrixBackground />
      <BackButton onClick={handleBack} label={view === "text" ? "Graph" : "Back"} />
      <Header nodeCount={nodes.length} edgeCount={edges.length} />

      <main className="liquid-glass relative z-10 mt-4 flex w-full max-w-5xl flex-1 flex-col overflow-hidden rounded-2xl border border-hairline bg-panel shadow-glass backdrop-blur-glass">
        {loading ? (
          <div className="flex flex-1 items-center justify-center text-sm text-white/40">
            Computing the synapse graph…
          </div>
        ) : (
          <div className="relative h-[70vh] min-h-[420px] w-full">
            <div
              className={`absolute inset-0 transition-opacity duration-300 ${
                view === "graph" ? "opacity-100" : "pointer-events-none opacity-0"
              }`}
            >
              <GraphCanvas
                ref={graphRef}
                nodes={nodes}
                edges={edges}
                onNodeClick={openNode}
              />
              <Legend tierCounts={tierCounts} />
              <SearchBar onSearch={handleSearch} />
            </div>

            <div
              className={`absolute inset-0 transition-opacity duration-300 ${
                view === "text" ? "opacity-100" : "pointer-events-none opacity-0"
              }`}
            >
              <NodeDetailView
                node={activeNode}
                edges={activeNode ? edgesByNode.get(activeNode.id) ?? [] : []}
                nodesById={nodesById}
                onJump={openNode}
              />
            </div>
          </div>
        )}
      </main>

      <p className="relative z-10 mt-4 text-center text-xs text-white/30">
        {usingLiveBackend
          ? `${nodes.length} nodes · ${edges.length} AI-formed synapse connections — live from the Obsidian Backend.`
          : `${nodes.length} nodes · ${edges.length} synapse connections computed locally — start the Obsidian Backend (see Backend/README.md) for the full AI-driven graph.`}
      </p>
    </div>
  );
}
