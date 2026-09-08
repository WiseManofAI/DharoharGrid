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
import { GROUP_META } from "../lib/textUtils";

const COLOR_DEFAULT = "#ffffff";
const COLOR_HOVER = "#a78bfa"; // violet
const FADE_ALPHA = 0.1;
const HOVER_HIT_PADDING = 3; // px added around the drawn node for easier hover

// Confidence-tier palette straight from the Master Spec §5 trust model.
export const TIER_META = {
  verified: { color: "#f0cf83", label: "Verified", dash: null, width: 1.6 },
  source_supported: { color: "#8bb2ff", label: "Source-supported", dash: null, width: 1.3 },
  potential: { color: "#e2b357", label: "Potential (research lead)", dash: [1, 3], width: 1 },
  contradictory: { color: "#ef4444", label: "Contradictory", dash: [4, 2], width: 1.3 },
};

function nodeColor(node) {
  return GROUP_META[node.group]?.color ?? COLOR_DEFAULT;
}

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
  // a collide force so nodes never overlap, and two nested clustering
  // forces — a weak pull toward each node's heritage-type centroid (the
  // three superclusters) and a stronger pull toward its subtype-cluster
  // centroid (Forts & Castles, GI-Tagged Handicrafts, etc.) — so the
  // supercluster/subcluster taxonomy is visible directly in the layout,
  // not just as metadata. Plus enough damping that the layout settles
  // instead of oscillating forever.
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;

    fg.d3Force("charge")?.strength(-70).distanceMax(400);
    fg.d3Force("link")?.distance(42).strength(0.55);
    fg.d3Force(
      "collide",
      forceCollide((node) => nodeRadius(node.id) + 3)
    );
    fg.d3Force("clusterHeritage", makeClusterForce(() => graphData.nodes, (n) => n.group, 0.02));
    fg.d3Force("clusterSubtype", makeClusterForce(() => graphData.nodes, (n) => n.subtypeClusterId, 0.09));
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
        warmupTicks={60}
        cooldownTime={3200}
        d3AlphaDecay={0.045}
        d3VelocityDecay={0.5}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const r = nodeRadius(node.id);
          const dimmed = isDimmed(node.id);
          const isHovered = node.id === hoverId;

          ctx.globalAlpha = dimmed ? FADE_ALPHA : 0.92;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
          ctx.fillStyle = isHovered ? COLOR_HOVER : nodeColor(node);
          ctx.fill();
          if (isHovered) {
            ctx.lineWidth = 1.4 / globalScale;
            ctx.strokeStyle = "rgba(255,255,255,0.85)";
            ctx.stroke();
          }

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
          const base = TIER_META[link.tier]?.color ?? COLOR_DEFAULT;
          return dimmed ? `${base}${toAlphaHex(FADE_ALPHA)}` : `${base}${toAlphaHex(0.65)}`;
        }}
        linkWidth={(link) =>
          hoverId && activeLinks?.has(link.id) ? 2.2 : TIER_META[link.tier]?.width ?? 1
        }
        linkLineDash={(link) => TIER_META[link.tier]?.dash ?? null}
      />
    </div>
  );
});

// A minimal d3-force-compatible custom force: each tick, nodes sharing the
// same keyFn(node) value get nudged toward their group's current centroid.
// Two of these registered at different strengths (see the physics effect
// above) is what produces nested supercluster/subcluster visual grouping —
// this is the standard "cluster force" pattern from d3-force examples,
// just parameterized by an arbitrary key instead of a hardcoded field.
function makeClusterForce(getNodes, keyFn, strength) {
  return function force(alpha) {
    const nodes = getNodes();
    const centroids = new Map();
    for (const n of nodes) {
      const key = keyFn(n);
      if (!key || typeof n.x !== "number") continue;
      let c = centroids.get(key);
      if (!c) {
        c = { x: 0, y: 0, count: 0 };
        centroids.set(key, c);
      }
      c.x += n.x;
      c.y += n.y;
      c.count += 1;
    }
    centroids.forEach((c) => {
      c.x /= c.count;
      c.y /= c.count;
    });
    for (const n of nodes) {
      const key = keyFn(n);
      if (!key || typeof n.x !== "number") continue;
      const c = centroids.get(key);
      if (!c) continue;
      n.vx = (n.vx || 0) + (c.x - n.x) * alpha * strength;
      n.vy = (n.vy || 0) + (c.y - n.y) * alpha * strength;
    }
  };
}

function toAlphaHex(alpha) {
  return Math.round(alpha * 255)
    .toString(16)
    .padStart(2, "0");
}

export default GraphCanvas;
