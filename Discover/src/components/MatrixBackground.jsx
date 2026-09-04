import { useEffect, useRef } from "react";

const SPACING = 28;
const INFLUENCE_RADIUS = 150;
const MAX_DISTORTION = 14;
const BASE_ALPHA = 0.12;
const GLOW_BOOST = 0.07; // exactly the 7% soft glow boost used on the parent site

/**
 * Full-viewport dotted matrix background, matching the parent DharoharGrid
 * site's hero canvas: a grid of dots that bends away from the cursor within
 * INFLUENCE_RADIUS, brightening by a 7% soft glow as they get closer.
 * Fixed behind all UI, pointer-events disabled so it never blocks clicks.
 */
export default function MatrixBackground() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ worldX: -9999, worldY: -9999 });

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let animationFrame;

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    function handleMouseMove(e) {
      mouseRef.current.worldX = e.clientX;
      mouseRef.current.worldY = e.clientY;
    }
    function handleMouseLeave() {
      mouseRef.current.worldX = -9999;
      mouseRef.current.worldY = -9999;
    }
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseleave", handleMouseLeave);

    function render() {
      const { worldX, worldY } = mouseRef.current;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const cols = Math.ceil(canvas.width / SPACING);
      const rows = Math.ceil(canvas.height / SPACING);

      for (let r = 0; r <= rows; r++) {
        for (let c = 0; c <= cols; c++) {
          const originX = c * SPACING;
          const originY = r * SPACING;

          const dx = worldX - originX;
          const dy = worldY - originY;
          const dist = Math.hypot(dx, dy);

          let drawX = originX;
          let drawY = originY;
          let alpha = BASE_ALPHA;
          let size = 1;

          if (dist < INFLUENCE_RADIUS && dist > 0) {
            const factor = 1 - dist / INFLUENCE_RADIUS;
            const displacement = factor * factor * MAX_DISTORTION;

            drawX -= (dx / dist) * displacement;
            drawY -= (dy / dist) * displacement;
            alpha = BASE_ALPHA + GLOW_BOOST * factor;
            size = 1 + factor * 1.5;
          }

          ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
          ctx.beginPath();
          ctx.arc(drawX, drawY, size, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      animationFrame = requestAnimationFrame(render);
    }
    animationFrame = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0"
      aria-hidden="true"
    />
  );
}
