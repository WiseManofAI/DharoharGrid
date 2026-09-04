import { useMemo, useRef, useState } from "react";
import Header from "./components/Header";
import BackButton from "./components/BackButton";
import SearchBar from "./components/SearchBar";
import GraphCanvas from "./components/GraphCanvas";
import NodeDetailView from "./components/NodeDetailView";
import MatrixBackground from "./components/MatrixBackground";
import { useDharoharData } from "./hooks/useDharoharData";

// Where the "Back" button returns to — the parent site's Discover section.
// Swap for a router navigate() if this app is mounted inside the same SPA
// instead of being linked to as a standalone deployment.
const PARENT_SITE_URL = "/index.html";

export default function App() {
  const { nodes, edges, loading, usingMockData } = useDharoharData();
  const [view, setView] = useState("graph"); // "graph" | "text"
  const [activeNodeId, setActiveNodeId] = useState(null);
  const graphRef = useRef(null);

  const activeNode = useMemo(
    () => nodes.find((n) => n.id === activeNodeId) ?? null,
    [nodes, activeNodeId]
  );

  function handleNodeClick(nodeId) {
    setActiveNodeId(nodeId);
    setView("text");
  }

  function handleSearch(query) {
    graphRef.current?.focusNode(query);
  }

  function handleBack() {
    if (view === "text") {
      // Phase 4: Back closes the text view and returns to the graph first.
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
      <Header />

      <main className="relative z-10 mt-4 flex w-full max-w-5xl flex-1 flex-col overflow-hidden rounded-2xl border border-hairline bg-panel shadow-glass backdrop-blur-glass">
        {loading ? (
          <div className="flex flex-1 items-center justify-center text-sm text-white/40">
            Loading heritage graph…
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
                onNodeClick={handleNodeClick}
              />
              <SearchBar onSearch={handleSearch} />
            </div>

            <div
              className={`absolute inset-0 transition-opacity duration-300 ${
                view === "text" ? "opacity-100" : "pointer-events-none opacity-0"
              }`}
            >
              <NodeDetailView node={activeNode} />
            </div>
          </div>
        )}
      </main>

      {usingMockData && (
        <p className="relative z-10 mt-4 text-center text-xs text-white/30">
          Showing sample data — connect Supabase (see .env.example) to load
          the live DharoharGrid.
        </p>
      )}
    </div>
  );
}
