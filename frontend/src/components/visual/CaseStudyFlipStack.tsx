"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { Anchor, Navigation, ShieldAlert, LineChart, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export interface CaseStudyItem {
  id: string;
  category: string;
  title: string;
  subtitle: string;
  summary: string;
  scenario: string;
  resolution: string;
  icon: React.ElementType;
  accentColor: string;
  bgColor: string;
  stats: { label: string; value: string }[];
}

interface CaseStudyFlipStackProps {
  heading?: string;
  hint?: string;
  endLabel?: string;
  items?: CaseStudyItem[];
  className?: string;
}

const DEFAULT_ITEMS: CaseStudyItem[] = [
  {
    id: "fisheries",
    category: "FISHERIES",
    title: "From scattered forecasts to one safer trip decision.",
    subtitle: "Coastal Small-Craft Pre-Departure Advisory",
    summary:
      "A traditional artisanal crew in coastal Karnataka faced conflicting high-wave alerts and local weather predictions before a 4:00 AM launch.",
    scenario:
      "IMD reported moderate swell 20km offshore while local wind was calm. Traditional phone apps provided no vessel-specific advisory.",
    resolution:
      "Sagarvani cross-referenced INCOIS wave buoys and Doppler radar to determine a safe 8-hour window within 8 nautical miles, delivered in Kannada audio over helpline.",
    icon: Anchor,
    accentColor: "#00FFFF",
    bgColor: "#0B1550",
    stats: [
      { label: "Data Sources Fused", value: "3 Real-time" },
      { label: "Risk Verdict", value: "Window Safe" },
    ],
  },
  {
    id: "maritime",
    category: "MARITIME OPERATIONS",
    title: "Bring sea state, weather and spatial risk into one route view.",
    subtitle: "Commercial Coastal Transit Optimization",
    summary:
      "A coastal feeder vessel operating between Cochin and Mangalore needed to balance transit fuel economy against an approaching monsoon squall.",
    scenario:
      "Standard routing ignored bathymetric current corridors, forcing either excessive fuel burn or risky swell exposure.",
    resolution:
      "ORCA's Marine Data Agent combined surface currents with the Risk Agent's squall track, suggesting a 4-degree offshore diversion that saved 14% fuel while avoiding 3.5m wave peaks.",
    icon: Navigation,
    accentColor: "#38BDF8",
    bgColor: "#050A30",
    stats: [
      { label: "Transit Time Delta", value: "+12 min" },
      { label: "Max Wave Encounter", value: "1.8m (Safe)" },
    ],
  },
  {
    id: "disaster",
    category: "DISASTER MANAGEMENT",
    title: "Turn multiple warning feeds into one explainable operational picture.",
    subtitle: "Pre-Cyclone Hazard Preparedness",
    summary:
      "District emergency managers required an unified operational picture during rapid depression intensification in the Bay of Bengal.",
    scenario:
      "Disparate bulletins arrived from multiple agencies with differing lead times and spatial coordinates for sea-surge impact.",
    resolution:
      "Sagarvani fused IMD cyclone tracks with INCOIS coastal surge models and ISRO Bhuvan elevation layers, delivering an evidence-backed spatial impact map with 0 contradictions.",
    icon: ShieldAlert,
    accentColor: "#FFB020",
    bgColor: "#02051C",
    stats: [
      { label: "Harmonized Sources", value: "5 Agencies" },
      { label: "Synthesis Speed", value: "< 2.0s" },
    ],
  },
  {
    id: "science",
    category: "OCEAN SCIENCE",
    title: "Explore marine signals across sources without jumping between systems.",
    subtitle: "Multi-Sensor Oceanographic Research",
    summary:
      "Marine researchers investigating coastal upwelling and Chlorophyll-a anomalies needed direct correlation with sea surface salinity data.",
    scenario:
      "Data resided across separate portals (MOSDAC, Bhoonidhi, INCOIS), requiring manual CSV extraction and normalization.",
    resolution:
      "Researchers queried Sagarvani naturally, extracting validated correlation traces with verifiable source metadata and spatial coordinates ready for publication.",
    icon: LineChart,
    accentColor: "#A78BFA",
    bgColor: "#08103A",
    stats: [
      { label: "Citation Provenance", value: "100% Traceable" },
      { label: "Parameters Fused", value: "SST + Chl-a + Sal" },
    ],
  },
];

function FlipCard({
  item,
  index,
  total,
  scrollYProgress,
}: {
  item: CaseStudyItem;
  index: number;
  total: number;
  scrollYProgress: any;
}) {
  const shouldReduceMotion = useReducedMotion();
  const Icon = item.icon;

  const targetScale = 1 - (total - index - 1) * 0.04;
  const startRange = index / total;
  const endRange = (index + 1) / total;

  const scale = useTransform(scrollYProgress, [startRange, endRange], [1, targetScale]);
  const y = useTransform(scrollYProgress, [startRange, endRange], [0, -index * 15]);

  return (
    <div className="sticky top-28 mb-8 flex w-full justify-center">
      <motion.div
        style={{
          ...(shouldReduceMotion ? {} : { scale, y }),
          backgroundColor: item.bgColor,
          boxShadow: `0 25px 60px -15px ${item.accentColor}15, 0 0 0 1px var(--color-border)`,
        }}
        className="relative w-full max-w-4xl overflow-hidden rounded-2xl border border-border p-8 md:p-12 shadow-2xl transition-all duration-300"
      >
        {/* Top Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-6">
          <div className="flex items-center gap-3">
            <div
              className="flex h-12 w-12 items-center justify-center rounded-xl border"
              style={{
                backgroundColor: `${item.accentColor}18`,
                borderColor: `${item.accentColor}40`,
                color: item.accentColor,
              }}
            >
              <Icon className="h-6 w-6" />
            </div>
            <div>
              <span
                className="font-mono text-xs font-bold tracking-widest uppercase"
                style={{ color: item.accentColor }}
              >
                {item.category}
              </span>
              <p className="text-sm font-medium text-white/70">{item.subtitle}</p>
            </div>
          </div>
          <span className="font-mono text-xs text-white/40">
            Scenario 0{index + 1} / 0{total}
          </span>
        </div>

        {/* Title */}
        <h3 className="mt-6 font-heading text-2xl font-bold leading-tight text-white md:text-3xl">
          {item.title}
        </h3>

        {/* Summary & Resolution Columns */}
        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="rounded-xl border border-white/10 bg-black/30 p-5">
            <span className="text-[11px] font-bold tracking-wider uppercase text-white/50 block mb-2">
              Operational Challenge
            </span>
            <p className="text-sm leading-relaxed text-white/80">{item.scenario}</p>
          </div>

          <div className="rounded-xl border border-white/10 bg-black/30 p-5">
            <span
              className="text-[11px] font-bold tracking-wider uppercase block mb-2"
              style={{ color: item.accentColor }}
            >
              ORCA Validated Resolution
            </span>
            <p className="text-sm leading-relaxed text-white/90">{item.resolution}</p>
          </div>
        </div>

        {/* Bottom Stats & Link */}
        <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-white/10 pt-6">
          <div className="flex flex-wrap gap-8">
            {item.stats.map((st) => (
              <div key={st.label}>
                <span className="block font-heading text-lg font-bold" style={{ color: item.accentColor }}>
                  {st.value}
                </span>
                <span className="text-[11px] uppercase tracking-wider text-white/50">{st.label}</span>
              </div>
            ))}
          </div>

          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-xs font-semibold hover:underline"
            style={{ color: item.accentColor }}
          >
            Explore this in the console <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </motion.div>
    </div>
  );
}

export function CaseStudyFlipStack({
  heading = "Decisions made clearer.",
  hint = "Scroll down to explore scenarios",
  endLabel = "One ocean. One decision layer.",
  items = DEFAULT_ITEMS,
  className,
}: CaseStudyFlipStackProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  return (
    <section
      ref={containerRef}
      className={cn(
        "relative border-b border-border bg-bg-sunken py-24 md:py-32",
        className
      )}
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-12">
        <div className="mb-20 text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-primary">
            Real-World Scenarios
          </span>
          <h2 className="mt-3 font-heading text-3xl font-bold text-foreground md:text-5xl">
            {heading}
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-text-secondary">{hint}</p>
        </div>

        {/* Stack of Cards */}
        <div className="relative pb-16">
          {items.map((item, index) => (
            <FlipCard
              key={item.id}
              item={item}
              index={index}
              total={items.length}
              scrollYProgress={scrollYProgress}
            />
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="font-heading text-sm font-semibold uppercase tracking-widest text-primary/80">
            {endLabel}
          </p>
        </div>
      </div>
    </section>
  );
}
