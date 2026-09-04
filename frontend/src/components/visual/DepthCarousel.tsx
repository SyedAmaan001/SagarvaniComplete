"use client";

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import gsap from "gsap";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

type DepthCarouselItem = string | { image: string; alt?: string };

interface NormalizedItem {
  image: string;
  alt: string;
}

interface DepthCarouselProps {
  items?: DepthCarouselItem[];
  cardWidth?: number;
  cardHeight?: number;
  radius?: number;
  tint?: string;
  depth?: number;
  spread?: number;
  tilt?: number;
  tiltDirection?: "left" | "right";
  perspective?: number;
  visibleCards?: number;
  falloff?: number;
  blur?: number;
  duration?: number;
  ease?: string;
  autoplay?: boolean;
  autoplayDelay?: number;
  loop?: boolean;
  showControls?: boolean;
  showIndicators?: boolean;
  onChange?: (index: number, item: NormalizedItem) => void;
  className?: string;
}

// ─── Layout math ─────────────────────────────────────────────────────────────

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

function shortCircularDist(d: number, count: number) {
  const half = count / 2;
  while (d > half) d -= count;
  while (d < -half) d += count;
  return d;
}

interface CardLayout {
  translateZ: number;
  translateX: number;
  rotateY: number;
  opacity: number;
  brightness: number;
  blur: number;
  zIndex: number;
  shown: boolean;
}

function computeLayout(
  d: number,
  opts: {
    depth: number;
    spread: number;
    tilt: number;
    direction: number;
    visibleCards: number;
    falloff: number;
    blur: number;
  }
): CardLayout {
  const { depth, spread, tilt, direction, visibleCards, falloff, blur } = opts;
  const back = Math.max(0, d);
  const absoluteD = Math.abs(d);
  const shown = absoluteD <= visibleCards + 0.5;

  const translateZ = -depth * d;
  const translateX = direction * spread * d;
  const rotateY = direction * tilt * clamp(d, 0, 1);

  let opacity: number;
  if (d < 0) {
    opacity = Math.max(0, 1 + d);
  } else {
    opacity = 1;
  }
  if (!shown) opacity = 0;

  const brightness = Math.max(0.15, 1 - back * falloff);
  const blurPx =
    blur > 0 ? Math.min(blur, (back / Math.max(1, visibleCards)) * blur) : 0;
  const zIndex = Math.round(2000 - d * 20);

  return { translateZ, translateX, rotateY, opacity, brightness, blur: blurPx, zIndex, shown };
}

// ─── Component ───────────────────────────────────────────────────────────────

export function DepthCarousel({
  items = [],
  cardWidth = 300,
  cardHeight = 380,
  radius = 18,
  tint = "#05060a",
  depth = 220,
  spread = 90,
  tilt = 22,
  tiltDirection = "right",
  perspective = 1400,
  visibleCards = 4,
  falloff = 0.2,
  blur = 6,
  duration = 700,
  ease = "power3.out",
  autoplay = false,
  autoplayDelay = 3200,
  loop = true,
  showControls = true,
  showIndicators = true,
  onChange,
  className,
}: DepthCarouselProps) {
  // Normalize items
  const normalized: NormalizedItem[] = items.map((item) =>
    typeof item === "string" ? { image: item, alt: "" } : { image: item.image, alt: item.alt ?? "" }
  );
  const count = normalized.length;

  const rootRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const proxyRef = useRef({ p: 0 });
  const tweenRef = useRef<gsap.core.Tween | null>(null);
  const autoplayRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wheelTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [scale, setScale] = useState(1);
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const prefersReducedMotion =
    typeof window !== "undefined"
      ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
      : false;

  const direction = tiltDirection === "right" ? 1 : -1;

  // ── Layout pass ──────────────────────────────────────────────────────────
  const layoutCards = useCallback(
    (pos: number) => {
      if (!stageRef.current) return;
      const cards = stageRef.current.querySelectorAll<HTMLDivElement>("[data-card]");
      cards.forEach((card, i) => {
        let d = i - pos;
        if (loop) d = shortCircularDist(d, count);

        const layout = computeLayout(d, {
          depth,
          spread,
          tilt,
          direction,
          visibleCards,
          falloff,
          blur,
        });

        card.style.transform = [
          "translate(-50%, -50%)",
          `scale(${scale})`,
          `translateX(${layout.translateX}px)`,
          `translateZ(${layout.translateZ}px)`,
          `rotateY(${layout.rotateY}deg)`,
        ].join(" ");
        card.style.opacity = String(layout.opacity);
        card.style.filter = `brightness(${layout.brightness}) ${layout.blur > 0 ? `blur(${layout.blur}px)` : ""}`;
        card.style.zIndex = String(layout.zIndex);
        card.style.pointerEvents = layout.shown && layout.opacity > 0.15 ? "auto" : "none";
      });
    },
    [count, depth, spread, tilt, direction, visibleCards, falloff, blur, loop, scale]
  );

  // ── Navigate ─────────────────────────────────────────────────────────────
  const navigateTo = useCallback(
    (target: number) => {
      if (tweenRef.current) tweenRef.current.kill();

      tweenRef.current = gsap.to(proxyRef.current, {
        p: target,
        duration: prefersReducedMotion ? 0 : duration / 1000,
        ease,
        onUpdate() {
          const pos = proxyRef.current.p;
          const normalizedPos =
            loop && count > 0
              ? ((pos % count) + count) % count
              : pos;
          layoutCards(normalizedPos);
        },
        onComplete() {
          let finalPos = proxyRef.current.p;
          if (loop && count > 0) {
            finalPos = ((finalPos % count) + count) % count;
            proxyRef.current.p = finalPos;
          }
          const idx = Math.round(finalPos);
          const safeIdx = ((idx % count) + count) % count;
          setCurrentIndex(safeIdx);
          layoutCards(finalPos);
          onChange?.(safeIdx, normalized[safeIdx]);
        },
      });
    },
    [prefersReducedMotion, duration, ease, loop, count, layoutCards, onChange, normalized]
  );

  const prev = useCallback(() => {
    navigateTo(proxyRef.current.p - 1);
  }, [navigateTo]);

  const next = useCallback(() => {
    navigateTo(proxyRef.current.p + 1);
  }, [navigateTo]);

  // ── Responsive scale ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!rootRef.current) return;
    const observer = new ResizeObserver((entries) => {
      const w = entries[0].contentRect.width;
      const needed = cardWidth + Math.abs(spread) * 2 + 120;
      const s = clamp(w / needed, 0.4, 1);
      setScale(s);
    });
    observer.observe(rootRef.current);
    return () => observer.disconnect();
  }, [cardWidth, spread]);

  // Re-layout when scale changes
  useEffect(() => {
    const pos = proxyRef.current.p;
    const normalizedPos = loop && count > 0 ? ((pos % count) + count) % count : pos;
    layoutCards(normalizedPos);
  }, [scale, layoutCards, loop, count]);

  // Initial layout
  useEffect(() => {
    layoutCards(0);
  }, [layoutCards]);

  // ── Pointer drag ─────────────────────────────────────────────────────────
  const dragState = useRef({
    active: false,
    moved: false,
    startX: 0,
    startPos: 0,
    pointerId: -1,
    lastX: 0,
    lastTime: 0,
    velocity: 0,
  });

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (tweenRef.current) tweenRef.current.kill();
      const ds = dragState.current;
      ds.active = true;
      ds.moved = false;
      ds.startX = e.clientX;
      ds.startPos = proxyRef.current.p;
      ds.pointerId = e.pointerId;
      ds.lastX = e.clientX;
      ds.lastTime = performance.now();
      ds.velocity = 0;
    },
    []
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      const ds = dragState.current;
      if (!ds.active || e.pointerId !== ds.pointerId) return;
      const dx = e.clientX - ds.startX;
      if (!ds.moved && Math.abs(dx) > 4) {
        ds.moved = true;
        rootRef.current?.setPointerCapture(e.pointerId);
      }
      if (!ds.moved) return;

      const stepPx = Math.max(cardWidth * 0.55 * scale, 40);
      const pos = ds.startPos - dx / stepPx;
      proxyRef.current.p = pos;

      const now = performance.now();
      const dt = now - ds.lastTime;
      ds.velocity = dt > 0 ? (e.clientX - ds.lastX) / dt : 0;
      ds.lastX = e.clientX;
      ds.lastTime = now;

      const normalizedPos = loop && count > 0 ? ((pos % count) + count) % count : pos;
      layoutCards(normalizedPos);
    },
    [cardWidth, scale, loop, count, layoutCards]
  );

  const onPointerUp = useCallback(() => {
    const ds = dragState.current;
    if (!ds.active) return;
    ds.active = false;

    if (!ds.moved) return;
    const stepPx = Math.max(cardWidth * 0.55 * scale, 40);
    const projected = proxyRef.current.p - (ds.velocity * 180) / stepPx;
    const target = Math.round(projected);
    navigateTo(target);
  }, [cardWidth, scale, navigateTo]);

  // ── Wheel ─────────────────────────────────────────────────────────────────
  const onWheel = useCallback(
    (e: React.WheelEvent) => {
      if (count < 2) return;
      e.preventDefault();
      const rawDelta =
        Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;
      const delta = e.deltaMode === 1 ? rawDelta * 24 : rawDelta;
      const step = clamp(delta / (cardWidth * 0.9), -0.6, 0.6);

      proxyRef.current.p += step;
      const pos = proxyRef.current.p;
      const normalizedPos = loop && count > 0 ? ((pos % count) + count) % count : pos;
      layoutCards(normalizedPos);

      if (wheelTimerRef.current) clearTimeout(wheelTimerRef.current);
      wheelTimerRef.current = setTimeout(() => {
        navigateTo(Math.round(proxyRef.current.p));
      }, 130);
    },
    [count, cardWidth, loop, layoutCards, navigateTo]
  );

  // ── Keyboard ─────────────────────────────────────────────────────────────
  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        prev();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        next();
      }
    },
    [prev, next]
  );

  // ── Autoplay ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!autoplay || prefersReducedMotion || count < 2) return;
    const delay = Math.max(autoplayDelay, 600);
    if (autoplayRef.current) clearInterval(autoplayRef.current);
    if (!isHovered && !isFocused) {
      autoplayRef.current = setInterval(() => next(), delay);
    }
    return () => {
      if (autoplayRef.current) clearInterval(autoplayRef.current);
    };
  }, [autoplay, autoplayDelay, prefersReducedMotion, count, isHovered, isFocused, next]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      tweenRef.current?.kill();
      if (autoplayRef.current) clearInterval(autoplayRef.current);
      if (wheelTimerRef.current) clearTimeout(wheelTimerRef.current);
    };
  }, []);

  if (count === 0) return null;

  return (
    <div
      ref={rootRef}
      role="group"
      aria-roledescription="carousel"
      aria-label="Agent depth carousel"
      tabIndex={0}
      className={cn("relative flex w-full select-none flex-col items-center outline-none", className)}
      style={{ height: cardHeight + 120 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onWheel={onWheel}
      onKeyDown={onKeyDown}
    >
      {/* 3D Stage */}
      <div
        className="relative flex-1 w-full"
        style={{ perspective: `${perspective}px`, perspectiveOrigin: "50% 50%" }}
      >
        <div
          ref={stageRef}
          className="absolute inset-0"
          style={{ transformStyle: "preserve-3d" }}
        >
          {normalized.map((item, i) => (
            <div
              key={i}
              data-card
              role="group"
              aria-roledescription="slide"
              aria-label={`${i + 1} of ${count}`}
              aria-hidden={currentIndex !== i}
              className="absolute left-1/2 top-1/2 overflow-hidden"
              style={{
                width: cardWidth,
                height: cardHeight,
                borderRadius: radius,
                background: tint,
                willChange: "transform",
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={item.image}
                alt={item.alt}
                draggable={false}
                className="h-full w-full object-cover"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Controls */}
      {showControls && count > 1 && (
        <>
          <button
            aria-label="Previous"
            onClick={(e) => {
              e.stopPropagation();
              prev();
            }}
            className="absolute left-2 top-1/2 z-50 flex h-[42px] w-[42px] -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white backdrop-blur-md transition-transform active:scale-95"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path
                fillRule="evenodd"
                d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
                clipRule="evenodd"
              />
            </svg>
          </button>
          <button
            aria-label="Next"
            onClick={(e) => {
              e.stopPropagation();
              next();
            }}
            className="absolute right-2 top-1/2 z-50 flex h-[42px] w-[42px] -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white backdrop-blur-md transition-transform active:scale-95"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path
                fillRule="evenodd"
                d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </>
      )}

      {/* Indicators */}
      {showIndicators && count > 1 && (
        <div
          role="tablist"
          aria-label="Carousel slides"
          className="mt-4 flex items-center gap-2"
        >
          {normalized.map((_, i) => (
            <button
              key={i}
              role="tab"
              aria-selected={i === currentIndex}
              aria-label={`Go to slide ${i + 1}`}
              onClick={() => navigateTo(i)}
              className="rounded-full transition-all duration-[250ms]"
              style={{
                width: i === currentIndex ? 20 : 7,
                height: 7,
                background:
                  i === currentIndex ? "white" : "rgba(255,255,255,0.3)",
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
