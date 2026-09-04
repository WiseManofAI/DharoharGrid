import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import ForceGraph2D from "react-force-graph-2d";
import { forceCollide } from "d3-force-3d";

const COLOR_DEFAULT = "#ffffff";
const COLOR_UNCONFIRMED = "#ef4444"; // AI-discovered, not yet confirmed
const COLOR_HOVER = "#a78bfa"; // violet
const FADE_ALPHA = 0.12;
const HOVER_HIT_PADDING = 3; // px added around the drawn node for easier hover

/**
 * Phase 3: force-directed graph (react-force-graph-2d) rendering the
 * Supabase-sourced nodes/edges with Obsidian-style visual rules:
 *  - node radius scales with degree (connection count)
 *  - AI-discovered/unconfirmed edges render red, confirmed edges white
 *  - hovering a node highlights it + its direct links in violet, fades the rest
 *  - exposes `focusNode(title)` via ref so the search bar (Phase 1) can pan +
 *    trigger the hover state on a match
 *
 * Physics + hover hit-testing are tuned to feel like Obsidian's native graph
 * view: nodes settle into evenly-spaced, non-overlapping clusters instead of
 * drifting/jittering, and the entire visible circle (not just its center
 * pixel) is hoverable.
 */
const GraphCanvas = forwardRef(function GraphCanvas(
  { nodes, edges, onNodeClick },
  ref
) {
  const fgRef = useRef(null);
  const containerRef = useRef(null);
  const [dims, setDims] = useState({ width: 600, height: 400 });
  const [hoverId, setHoverId] = useState(null);

  // Track container size so the canvas fills the glass tab responsively.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDims({ width, height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Degree + adjacency, computed from the raw (un-mutated) edges list —
  // react-force-graph rewrites link.source/target into node object refs, so
  // we keep our own id-keyed lookup for hover highlighting and sizing.
  const { degree, neighborNodeIds, neighborLinkIds } = useMemo(() => {
    const degree = new Map();
    const neighborNodeIds = new Map(); // nodeId -> Set of neighbor ids
    const neighborLinkIds = new Map(); // nodeId -> Set of link ids touching it

    nodes.forEach((n) => {
      degree.set(n.id, 0);
      neighborNodeIds.set(n.id, new Set());
      neighborLinkIds.set(n.id, new Set());
    });

    edges.forEach((e) => {
      degree.set(e.source, (degree.get(e.source) ?? 0) + 1);
      degree.set(e.target, (degree.get(e.target) ?? 0) + 1);
      neighborNodeIds.get(e.source)?.add(e.target);
      neighborNodeIds.get(e.target)?.add(e.source);
      neighborLinkIds.get(e.source)?.add(e.id);
      neighborLinkIds.get(e.target)?.add(e.id);
    });

    return { degree, neighborNodeIds, neighborLinkIds };
  }, [nodes, edges]);

  // react-force-graph mutates the objects it's given, so pass fresh copies
  // each time the source data changes rather than the raw props.
  const graphData = useMemo(
    () => ({
      nodes: nodes.map((n) => ({ ...n })),
      links: edges.map((e) => ({ ...e })),
    }),
    [nodes, edges]
  );

  const activeNeighbors = hoverId ? neighborNodeIds.get(hoverId) : null;
  const activeLinks = hoverId ? neighborLinkIds.get(hoverId) : null;

  function nodeRadius(nodeId) {
    const d = degree.get(nodeId) ?? 0;
    return 4 + Math.sqrt(d) * 2.6;
  }

  function isDimmed(nodeId) {
    if (!hoverId) return false;
    return nodeId !== hoverId && !activeNeighbors?.has(nodeId);
  }

  // Obsidian-like physics: strong-but-bounded repulsion, fixed-length links,
  // and a collide force so nodes never overlap — plus enough damping that
  // the layout settles instead of oscillating forever.
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;

    fg.d3Force("charge")?.strength(-140).distanceMax(600);
    fg.d3Force("link")?.distance(80).strength(0.6);
    fg.d3Force(
      "collide",
      forceCollide((node) => nodeRadius(node.id) + 6)
    );
    fg.d3ReheatSimulation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphData]);

  useImperativeHandle(ref, () => ({
    // Used by the search bar to pan the camera to a node and highlight it.
    focusNode(query) {
      const match = nodes.find((n) =>
        n.title.toLowerCase().includes(query.toLowerCase())
      );
      if (!match) return false;

      const point = graphData.nodes.find((n) => n.id === match.id);
      if (point && typeof point.x === "number" && fgRef.current) {
        fgRef.current.centerAt(point.x, point.y, 700);
        fgRef.current.zoom(4, 700);
      }
      setHoverId(match.id);
      return true;
    },
    clearFocus() {
      setHoverId(null);
    },
  }));

  return (
    <div ref={containerRef} className="h-full w-full">
      <ForceGraph2D
        ref={fgRef}
        width={dims.width}
        height={dims.height}
        graphData={graphData}
        backgroundColor="rgba(0,0,0,0)"
        nodeId="id"
        nodeLabel={(n) => n.title}
        nodeRelSize={1}
        onNodeHover={(node) => setHoverId(node ? node.id : null)}
        onNodeClick={(node) => onNodeClick?.(node.id)}
        linkDirectionalParticles={0}
        warmupTicks={80}
        cooldownTime={4000}
        d3AlphaDecay={0.03}
        d3VelocityDecay={0.45}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const r = nodeRadius(node.id);
          const dimmed = isDimmed(node.id);
          const isHovered = node.id === hoverId;

          ctx.globalAlpha = dimmed ? FADE_ALPHA : 1;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
          ctx.fillStyle = isHovered ? COLOR_HOVER : COLOR_DEFAULT;
          ctx.fill();

          // Label, shown once zoomed in enough (or always for hovered node)
          const showLabel = globalScale > 2.2 || isHovered;
          if (showLabel && !dimmed) {
            const fontSize = 11 / globalScale;
            ctx.font = `${fontSize}px -apple-system, sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            ctx.fillStyle = isHovered
              ? COLOR_HOVER
              : "rgba(255,255,255,0.85)";
            ctx.globalAlpha = 1;
            ctx.fillText(node.title, node.x, node.y + r + 2);
          }
          ctx.globalAlpha = 1;
        }}
        // Fixes hover only triggering at the exact center pixel: without
        // this, react-force-graph hit-tests against a tiny default hit
        // circle unrelated to the radius we actually draw above. This
        // paints the pick-color hit area at the same (padded) radius as
        // the visible node, on an off-screen canvas used purely for
        // pointer detection.
        nodePointerAreaPaint={(node, color, ctx) => {
          const r = nodeRadius(node.id) + HOVER_HIT_PADDING;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
        linkColor={(link) => {
          const dimmed = hoverId && !activeLinks?.has(link.id);
          if (hoverId && activeLinks?.has(link.id)) return COLOR_HOVER;
          const base =
            link.status === "ai_discovered"
              ? COLOR_UNCONFIRMED
              : COLOR_DEFAULT;
          return dimmed ? `${base}${toAlphaHex(FADE_ALPHA)}` : base;
        }}
        linkWidth={(link) => (hoverId && activeLinks?.has(link.id) ? 2 : 1)}
      />
    </div>
  );
});

function toAlphaHex(alpha) {
  return Math.round(alpha * 255)
    .toString(16)
    .padStart(2, "0");
}

export default GraphCanvas;
