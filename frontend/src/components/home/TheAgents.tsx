"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence, useScroll, useMotionValueEvent } from "framer-motion";
import { Waves, CloudRain, Map, LineChart, ShieldAlert, Compass, ChevronLeft, ChevronRight } from "lucide-react";
import { DepthCarousel } from "@/components/visual/DepthCarousel";
import { BorderGlow } from "@/components/visual/BorderGlow";

const AGENT_DATA = [
  {
    id: "01",
    num: "01 / 06",
    name: "Marine Data Agent",
    icon: Waves,
    accent: "#00FFFF",
    desc: "Currents, waves, SST, salinity, and core marine parameters from live oceanographic sensors.",
    image: "/images/agent_marine_data.jpg",
    tags: ["Wave Heights", "SST & Salinity", "Ocean Currents", "Live Sensors"],
    status: "Active Monitoring",
  },
  {
    id: "02",
    num: "02 / 06",
    name: "Weather Agent",
    icon: CloudRain,
    accent: "#60A5FA",
    desc: "Forecasts, wind vectors, barometric pressure, rainfall radar, and severe weather alerts.",
    image: "/images/agent_weather.jpg",
    tags: ["Wind Vectors", "Pressure Gradients", "Rain Radar", "Squall Alerts"],
    status: "Broadcasting Alerts",
  },
  {
    id: "03",
    num: "03 / 06",
    name: "GIS Agent",
    icon: Map,
    accent: "#34D399",
    desc: "Shorelines, bathymetry, EEZ boundaries, transit routes, and coastal points of interest.",
    image: "/images/agent_gis.jpg",
    tags: ["Bathymetry", "EEZ Boundaries", "Shipping Lanes", "Coastal Topology"],
    status: "Spatial Mapping",
  },
  {
    id: "04",
    num: "04 / 06",
    name: "Ocean Analytics Agent",
    icon: LineChart,
    accent: "#F472B6",
    desc: "Multi-sensor time-series patterns, anomaly clustering, and historical marine trend discovery.",
    image: "/images/agent_analytics.jpg",
    tags: ["Time Series", "Anomaly Clustering", "Historical Models", "Pattern Recognition"],
    status: "Pattern Analysis",
  },
  {
    id: "05",
    num: "05 / 06",
    name: "Risk Agent",
    icon: ShieldAlert,
    accent: "#FB923C",
    desc: "Cyclone tracks, dynamic surge buffers, pollution zones, and vessel navigation hazards.",
    image: "/images/agent_risk.jpg",
    tags: ["Surge Buffers", "Cyclone Vectors", "Pollution Track", "Hazard Scoring"],
    status: "Hazard Evaluation",
  },
  {
    id: "06",
    num: "06 / 06",
    name: "Spatial Reasoning Agent",
    icon: Compass,
    accent: "#A78BFA",
    desc: "Topological relations, proximity buffers, safety corridors, and geographic constraint checking.",
    image: "/images/agent_spatial.jpg",
    tags: ["Safety Corridors", "Proximity Check", "Topological Graph", "Constraint Logic"],
    status: "Constraint Verification",
  },
];

export function TheAgents() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  // Scroll tracking
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    const computedIndex = Math.min(
      Math.floor(latest * AGENT_DATA.length),
      AGENT_DATA.length - 1
    );
    if (computedIndex !== activeIndex) {
      setActiveIndex(computedIndex);
    }
  });

  const goToAgent = useCallback((index: number) => {
    setActiveIndex(index);
    if (!containerRef.current) return;
    const containerTop = containerRef.current.offsetTop;
    const containerHeight = containerRef.current.offsetHeight;
    const stepHeight = containerHeight / AGENT_DATA.length;
    const targetScroll = containerTop + stepHeight * index + stepHeight * 0.2;
    window.scrollTo({ top: targetScroll, behavior: "smooth" });
  }, []);

  const handlePrev = useCallback(() => {
    if (activeIndex > 0) goToAgent(activeIndex - 1);
  }, [activeIndex, goToAgent]);

  const handleNext = useCallback(() => {
    if (activeIndex < AGENT_DATA.length - 1) goToAgent(activeIndex + 1);
  }, [activeIndex, goToAgent]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handlePrev, handleNext]);

  const activeAgent = AGENT_DATA[activeIndex];

  return (
    <section
      id="agents"
      ref={containerRef}
      className="relative bg-bg-sunken border-b border-border"
      style={{ height: `${AGENT_DATA.length * 85}vh` }}
    >
      {/* Sticky Viewport */}
      <div className="sticky top-0 h-screen flex flex-col justify-between py-8 md:py-12 overflow-hidden">
        {/* Background Ambient Glow tailored to active agent accent */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 transition-all duration-700 opacity-20"
          style={{
            background: `radial-gradient(circle at 40% 50%, ${activeAgent.accent} 0%, transparent 65%)`,
          }}
        />

        {/* Section Header */}
        <div className="mx-auto max-w-7xl px-6 lg:px-12 relative z-10 w-full text-center shrink-0 mb-4">
          <span className="text-xs md:text-sm font-semibold uppercase tracking-wider text-primary">
            THE AGENTS
          </span>
          <h2 className="mt-1 font-heading text-2xl md:text-4xl font-bold text-foreground">
            Six specialists. One decision.
          </h2>
        </div>

        {/* Main Showcase Grid */}
        <div className="mx-auto max-w-7xl px-6 lg:px-12 relative z-10 w-full flex-1 flex flex-col justify-center min-h-0">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
            
            {/* Left Side: 3D Depth Carousel Container */}
            <div className="lg:col-span-7 flex justify-center items-center relative">
              <BorderGlow
                colors={[activeAgent.accent, "#0000FF", "#60A5FA"]}
                glowColor="190 100 60"
                backgroundColor="#02051C"
                borderRadius={24}
                glowRadius={50}
                glowIntensity={0.6}
                className="w-full rounded-2xl border border-border p-3 shadow-2xl relative"
              >
                <div className="py-2">
                  <DepthCarousel
                    items={AGENT_DATA.map((a) => ({ image: a.image, alt: a.name }))}
                    cardWidth={340}
                    cardHeight={240}
                    depth={180}
                    spread={70}
                    tilt={15}
                    tiltDirection="right"
                    perspective={1200}
                    visibleCards={3}
                    falloff={0.25}
                    blur={4}
                    duration={600}
                    ease="power3.out"
                    autoplay={false}
                    loop={false}
                    showControls={false}
                    showIndicators={false}
                    onChange={(idx) => {
                      if (idx !== activeIndex) {
                        goToAgent(idx);
                      }
                    }}
                  />
                </div>
              </BorderGlow>
            </div>

            {/* Right Side: Active Agent Information */}
            <div className="lg:col-span-5 flex flex-col justify-center">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeAgent.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  {/* Agent Number / Index */}
                  <div className="flex items-center gap-3">
                    <span
                      className="font-mono text-2xl font-bold tracking-wider"
                      style={{ color: activeAgent.accent }}
                    >
                      {activeAgent.num}
                    </span>
                    <div className="h-px flex-1 bg-border" />
                  </div>

                  {/* Agent Name */}
                  <h3 className="font-heading font-bold text-2xl md:text-4xl text-foreground">
                    {activeAgent.name}
                  </h3>

                  {/* Agent Description */}
                  <p className="text-text-secondary text-base md:text-lg leading-relaxed">
                    {activeAgent.desc}
                  </p>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-2 pt-2">
                    {activeAgent.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs font-mono px-3 py-1 rounded-md bg-bg-elevated border border-border text-text-secondary"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Navigation & Progress Bar Footer */}
        <div className="mx-auto max-w-7xl px-6 lg:px-12 relative z-10 w-full shrink-0 mt-4">
          <div className="flex items-center justify-between border-t border-border pt-4">
            
            {/* Step Indicators */}
            <div className="flex items-center gap-2 overflow-x-auto py-1">
              {AGENT_DATA.map((agent, i) => (
                <button
                  key={agent.id}
                  onClick={() => goToAgent(i)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono transition-all duration-200 ${
                    i === activeIndex
                      ? "bg-primary/20 border border-primary text-primary font-bold"
                      : "bg-bg-elevated border border-border text-text-secondary hover:text-foreground"
                  }`}
                >
                  <span>{agent.id}</span>
                  <span className="hidden sm:inline">{agent.name.replace(" Agent", "")}</span>
                </button>
              ))}
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrev}
                disabled={activeIndex === 0}
                aria-label="Previous Agent"
                className="p-2 rounded-lg border border-border bg-bg-elevated text-text-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft size={20} />
              </button>
              <button
                onClick={handleNext}
                disabled={activeIndex === AGENT_DATA.length - 1}
                aria-label="Next Agent"
                className="p-2 rounded-lg border border-border bg-bg-elevated text-text-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

