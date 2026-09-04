"use client";

import React, { useEffect, useRef, RefObject } from "react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

interface CardPanel {
  title: string;
  description: string;
  bgColor: string;
  textColor: string;
}

interface ScrollSplitCardProps {
  containerRef?: RefObject<HTMLDivElement | null>;
  imageSrc?: string;
  cards?: CardPanel[];
  className?: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function ScrollSplitCard({
  containerRef,
  imageSrc,
  cards = [],
  className,
}: ScrollSplitCardProps) {
  const sectionRef = useRef<HTMLDivElement>(null);
  const panelsRef = useRef<HTMLDivElement[]>([]);
  const animRef = useRef<ReturnType<typeof import("animejs")["animate"]> | null>(null);

  useEffect(() => {
    let anime: typeof import("animejs");
    let observer: IntersectionObserver;
    let scrollEl: HTMLElement;
    let running = false;

    const scrollSource = containerRef?.current ?? window;

    const panels = panelsRef.current;
    if (!panels.length) return;

    // Reset initial positions
    panels.forEach((el, i) => {
      if (!el) return;
      el.style.transform = `translateZ(0px) rotateY(0deg)`;
      el.style.opacity = "1";
    });

    async function init() {
      anime = await import("animejs");

      function onScroll() {
        const section = sectionRef.current;
        if (!section) return;

        const scrollTop =
          containerRef?.current
            ? containerRef.current.scrollTop
            : window.scrollY;
        const rect = section.getBoundingClientRect();
        const sectionTop =
          containerRef?.current
            ? section.offsetTop - containerRef.current.scrollTop
            : rect.top + window.scrollY - window.scrollY;

        const vh = window.innerHeight;
        const progress = Math.max(
          0,
          Math.min(
            1,
            (scrollTop - (section.offsetTop - vh)) /
              (section.offsetHeight + vh * 0.5)
          )
        );

        // Three panels: split apart as progress advances
        const p3 = panels[2];
        const p1 = panels[0];
        const p2 = panels[1];

        if (p1 && p2 && p3) {
          // Phase 1 (0–0.33): front panel reveals
          const phase1 = Math.min(1, progress / 0.33);
          // Phase 2 (0.33–0.66): middle panel rises
          const phase2 = Math.min(1, Math.max(0, (progress - 0.33) / 0.33));
          // Phase 3 (0.66–1): back panel appears
          const phase3 = Math.min(1, Math.max(0, (progress - 0.66) / 0.34));

          p1.style.transform = `
            perspective(1200px)
            translateY(${-phase1 * 60}px)
            translateZ(${phase1 * 80}px)
            rotateX(${phase1 * -4}deg)
          `;
          p1.style.opacity = `${0.7 + phase1 * 0.3}`;

          p2.style.transform = `
            perspective(1200px)
            translateY(${phase2 * 40}px)
            translateZ(${-phase2 * 40}px)
            rotateX(${phase2 * 2}deg)
          `;
          p2.style.opacity = `${0.5 + phase2 * 0.5}`;

          p3.style.transform = `
            perspective(1200px)
            translateY(${-phase3 * 30}px)
            translateZ(${-phase3 * 100}px)
            rotateX(${phase3 * 6}deg)
          `;
          p3.style.opacity = `${phase3}`;
        }
      }

      scrollSource.addEventListener("scroll", onScroll, { passive: true });
      onScroll(); // Initial run

      observer = new IntersectionObserver(
        (entries) => {
          running = entries[0].isIntersecting;
        },
        { threshold: 0.1 }
      );
      if (sectionRef.current) observer.observe(sectionRef.current);
    }

    init();

    return () => {
      if (observer) observer.disconnect();
      scrollSource.removeEventListener("scroll", () => {});
    };
  }, [containerRef]);

  const panelColors = [
    cards[0] ?? { bgColor: "#e2e2e2", textColor: "#111111", title: "Phase 1", description: "First stage." },
    cards[1] ?? { bgColor: "#1a5bcf", textColor: "#ffffff", title: "Phase 2", description: "Second stage." },
    cards[2] ?? { bgColor: "#1c1c1c", textColor: "#ffffff", title: "Phase 3", description: "Third stage." },
  ];

  return (
    <div
      ref={sectionRef}
      className={cn("relative flex items-center justify-center py-24", className)}
    >
      <div
        className="relative mx-auto"
        style={{ width: 340, height: 460, transformStyle: "preserve-3d" }}
      >
        {panelColors.map((panel, i) => (
          <div
            key={i}
            ref={(el) => {
              if (el) panelsRef.current[i] = el;
            }}
            className="absolute inset-0 flex flex-col justify-end overflow-hidden rounded-2xl p-8 shadow-2xl"
            style={{
              background: panel.bgColor,
              color: panel.textColor,
              zIndex: 3 - i,
              willChange: "transform, opacity",
              transition: "transform 0.05s linear, opacity 0.05s linear",
            }}
          >
            {imageSrc && i === 0 && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={imageSrc}
                alt=""
                className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-30"
              />
            )}
            <div className="relative z-10">
              <h3 className="font-heading text-2xl font-bold leading-tight">
                {panel.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed opacity-80">
                {panel.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
