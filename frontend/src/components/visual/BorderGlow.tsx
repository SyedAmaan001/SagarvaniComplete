"use client";

import {
  ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { cn } from "@/lib/utils";

interface BorderGlowProps {
  children?: ReactNode;
  className?: string;
  edgeSensitivity?: number;
  glowColor?: string;
  backgroundColor?: string;
  borderRadius?: number;
  glowRadius?: number;
  glowIntensity?: number;
  coneSpread?: number;
  animated?: boolean;
  colors?: string[];
  fillOpacity?: number;
}

function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "");
  const n = parseInt(clean, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function isLightColor(hex: string): boolean {
  const [r, g, b] = hexToRgb(hex);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 180;
}

function buildMeshGradient(colors: string[], positions: string[]): string {
  const gradients = positions.map((pos, i) => {
    const color = colors[i % colors.length];
    return `radial-gradient(at ${pos}, ${color} 0px, transparent 50%)`;
  });
  gradients.push(`linear-gradient(${colors[0]} 0 100%)`);
  return gradients.join(", ");
}

const MESH_POSITIONS = [
  "80% 55%",
  "69% 34%",
  "8% 6%",
  "41% 38%",
  "86% 85%",
  "82% 18%",
  "51% 4%",
];

export function BorderGlow({
  children,
  className,
  edgeSensitivity = 30,
  glowColor = "40 80 80",
  backgroundColor = "#120F17",
  borderRadius = 28,
  glowRadius = 40,
  glowIntensity = 1.0,
  coneSpread = 25,
  animated = false,
  colors = ["#c084fc", "#f472b6", "#38bdf8"],
  fillOpacity = 0.5,
}: BorderGlowProps) {
  const rootRef = useRef<HTMLDivElement>(null);

  // pointer state
  const [angle, setAngle] = useState(0);
  const [edgeProximity, setEdgeProximity] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [sweepActive, setSweepActive] = useState(false);
  const [sweepAngle, setSweepAngle] = useState(110);
  const [sweepProximity, setSweepProximity] = useState(0);

  const colorSensitivity = edgeSensitivity + 20;
  const isLight = isLightColor(backgroundColor);
  const isVisible = isHovered || sweepActive;

  // Parse glowColor as "h s l"
  const [h, s, l] = glowColor.split(" ").map(Number);
  const glowHsl = `hsl(${h}, ${s}%, ${l}%)`;

  // Build shadow layers
  const insetLayers = [
    [0, 1, 1.0],
    [1, 0, 0.6],
    [3, 0, 0.5],
    [6, 0, 0.4],
    [15, 0, 0.3],
    [25, 2, 0.2],
    [50, 2, 0.1],
  ];
  const outerLayers = [
    [1, 0, 0.6],
    [3, 0, 0.5],
    [6, 0, 0.4],
    [15, 0, 0.3],
    [25, 2, 0.2],
    [50, 2, 0.1],
  ];

  const buildShadow = (
    layers: number[][],
    inset: boolean,
    glowOpacity: number
  ) =>
    layers
      .map(([blur, spread, alpha]) => {
        const a = Math.min(1, alpha * glowIntensity);
        const rgba = `hsla(${h}, ${s}%, ${l}%, ${(a * glowOpacity).toFixed(2)})`;
        return `${inset ? "inset " : ""}0 0 ${blur}px ${spread}px ${rgba}`;
      })
      .join(", ");

  // Border opacity
  const borderOpacity = isVisible
    ? Math.max(
        0,
        (edgeProximity * 100 - colorSensitivity) / (100 - colorSensitivity)
      )
    : 0;
  const glowOpacity = isVisible
    ? Math.max(
        0,
        (edgeProximity * 100 - edgeSensitivity) / (100 - edgeSensitivity)
      )
    : 0;

  const displayAngle = sweepActive ? sweepAngle : angle;

  // Conic mask for directional border
  const coneMask = `conic-gradient(
    from ${displayAngle}deg at center,
    black ${coneSpread}%,
    transparent ${coneSpread + 15}%,
    transparent ${100 - coneSpread - 15}%,
    black ${100 - coneSpread}%
  )`;

  const meshBg = buildMeshGradient(colors, MESH_POSITIONS);

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!rootRef.current) return;
      const rect = rootRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const w = rect.width;
      const wh = rect.height;

      const cx = w / 2;
      const cy = wh / 2;
      const dx = x - cx;
      const dy = y - cy;

      const radians = Math.atan2(dy, dx);
      let deg = (radians * 180) / Math.PI + 90;
      if (deg < 0) deg += 360;
      setAngle(deg);

      // edge proximity: distance to nearest edge
      const distLeft = x;
      const distRight = w - x;
      const distTop = y;
      const distBottom = wh - y;
      const nearest = Math.min(distLeft, distRight, distTop, distBottom);
      const sensitivity = edgeSensitivity * 3;
      const proximity = Math.max(0, Math.min(1, 1 - nearest / sensitivity));
      setEdgeProximity(proximity);
    },
    [edgeSensitivity]
  );

  // Intro sweep animation
  useEffect(() => {
    if (!animated) return;
    setSweepActive(true);
    const start = performance.now();
    const totalDuration = 4000;

    const easeInCubic = (t: number) => t * t * t;
    const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

    let raf: number;
    const tick = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(1, elapsed / totalDuration);

      // phase 1: 0-500ms — proximity 0→1
      if (elapsed < 500) {
        setSweepProximity(elapsed / 500);
        setEdgeProximity(elapsed / 500);
      }
      // phase 2: 500-2000ms — angle 110→287
      else if (elapsed < 2000) {
        const ph = (elapsed - 500) / 1500;
        setSweepAngle(110 + 177 * easeInCubic(ph));
      }
      // phase 3: 2000-4250ms — continue to 465
      else if (elapsed < 4250) {
        const ph = (elapsed - 2000) / 2250;
        setSweepAngle(287 + 178 * easeOutCubic(ph));
      }
      // phase 4: 2500ms+ — proximity 1→0
      if (elapsed >= 2500) {
        const ph = Math.min(1, (elapsed - 2500) / 1500);
        const prox = 1 - ph;
        setSweepProximity(prox);
        setEdgeProximity(prox);
      }

      if (elapsed < totalDuration) {
        raf = requestAnimationFrame(tick);
      } else {
        setSweepActive(false);
        setSweepProximity(0);
        setEdgeProximity(0);
      }
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [animated]);

  const effectiveProximity = sweepActive ? sweepProximity : edgeProximity;
  const effectiveBorderOpacity = isVisible
    ? Math.max(
        0,
        (effectiveProximity * 100 - colorSensitivity) /
          (100 - colorSensitivity)
      )
    : 0;
  const effectiveGlowOpacity = isVisible
    ? Math.max(
        0,
        (effectiveProximity * 100 - edgeSensitivity) / (100 - edgeSensitivity)
      )
    : 0;

  const transition = isVisible
    ? "opacity 250ms ease-out"
    : "opacity 750ms ease-in-out";

  return (
    <div
      ref={rootRef}
      className={cn("relative", className)}
      style={{ borderRadius }}
      onPointerMove={onPointerMove}
      onPointerEnter={() => setIsHovered(true)}
      onPointerLeave={() => {
        setIsHovered(false);
        setEdgeProximity(0);
      }}
    >
      {/* Mesh gradient border layer */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          borderRadius,
          padding: 1,
          background: meshBg,
          opacity: effectiveBorderOpacity,
          transition,
          WebkitMaskImage: coneMask,
          maskImage: coneMask,
        }}
      >
        <div
          style={{
            borderRadius: borderRadius - 1,
            width: "100%",
            height: "100%",
            background: backgroundColor,
          }}
        />
      </div>

      {/* Masked edge fill tint */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
        style={{
          borderRadius,
          opacity: effectiveBorderOpacity * fillOpacity,
          transition,
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: meshBg,
            WebkitMaskImage: coneMask,
            maskImage: coneMask,
          }}
        />
      </div>

      {/* Outer glow wrapper */}
      <div
        aria-hidden
        className="pointer-events-none absolute"
        style={{
          inset: -glowRadius,
          borderRadius: borderRadius + glowRadius,
          opacity: effectiveGlowOpacity,
          transition,
          WebkitMaskImage: coneMask,
          maskImage: coneMask,
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: glowRadius,
            borderRadius,
            boxShadow: buildShadow(insetLayers, true, 1) +
              ", " +
              buildShadow(outerLayers, false, 1),
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}
