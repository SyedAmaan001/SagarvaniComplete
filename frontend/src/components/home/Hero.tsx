"use client";

import { useState } from "react";
import { WebGLLiquid } from "@/components/visual/WebGLLiquid";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { 
  Waves, 
  CloudRain, 
  Map, 
  LineChart, 
  ShieldAlert, 
  Compass,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Terminal,
  FileCheck,
  AlertTriangle,
  RefreshCw,
  Navigation,
  Globe,
  Radio,
  MapPin,
  Activity,
  Cpu,
  Layers,
  ShieldCheck,
  Zap,
  TrendingUp
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function Hero() {
  const [activeHeroScenario, setActiveHeroScenario] = useState<"safe" | "conflict">("safe");

  const specialists = [
    { name: "Marine Data", icon: Waves, color: "#00FFFF", metric: "1.1m Swell" },
    { name: "Weather", icon: CloudRain, color: "#60A5FA", metric: "12 kts WSW" },
    { name: "GIS Spatial", icon: Map, color: "#34D399", metric: "15nm EEZ" },
    { name: "Analytics", icon: LineChart, color: "#F472B6", metric: "SST 28.4°C" },
    { name: "Risk Agent", icon: ShieldAlert, color: "#FB923C", metric: "Risk: Low" },
    { name: "Spatial", icon: Compass, color: "#A78BFA", metric: "Clear Route" },
  ];

  return (
    <WebGLLiquid
      colorDeep="#02051C"
      colorMid="#050A30"
      colorHighlight="#00FFFF"
      speed={0.7}
      flowStrength={1.1}
      grain={0.035}
      contrast={1.15}
      opacity={0.96}
      reveal={true}
      revealDuration={1.3}
      subtitle="Built for Smart India Hackathon 2026 · Problem Statement SIH26176"
      title="Marine Intelligence, One Conversation Away"
      description="Sagarvani understands your question, gathers ocean, weather, and geospatial data, and reasons across every source to deliver a validated, explainable recommendation — accessible from smartphones to simple helplines."
    >
      {/* Action Buttons */}
      <div className="flex flex-col gap-4 sm:flex-row items-center">
        <Button
          asChild
          size="lg"
          className="bg-primary text-bg-sunken font-bold text-base px-8 py-6 rounded-xl hover:bg-primary/90 shadow-[0_0_30px_rgba(0,255,255,0.35)] hover:scale-[1.03] transition-transform duration-150"
        >
          <Link href="/dashboard" className="flex items-center gap-2">
            <Terminal className="size-5" />
            <span>Try Sagarvani</span>
          </Link>
        </Button>
        <Button
          asChild
          variant="outline"
          size="lg"
          className="border-border/80 text-foreground bg-bg-elevated/50 hover:bg-bg-elevated hover:text-primary transition-colors py-6 px-7 rounded-xl"
        >
          <Link href="#how-it-works" className="flex items-center gap-2">
            <span>See How It Works</span>
            <ArrowRight className="size-4" />
          </Link>
        </Button>
      </div>

      {/* 
        ═════════════════════════════════════════════════════════════════════════
        CINEMATIC MARINE CONTROL-SYSTEM VISUALIZATION
        - Left Peripheral Support UI (Partially cropped / off-screen)
        - Dominant Central Ocean Intelligence Viewport (Map / Satellite / Depth)
        - Right Peripheral Support UI (Partially cropped / off-screen)
        - Floating Glassmorphic ORCA Intelligence Card in the Center
        ═════════════════════════════════════════════════════════════════════════
      */}
      <div className="mt-14 w-full max-w-[1400px] relative px-2 sm:px-4 lg:px-6">
        
        {/* Scenario Switcher Float Pill */}
        <div className="flex justify-center mb-6 relative z-30">
          <div className="inline-flex items-center gap-1.5 p-1.5 rounded-2xl bg-[#080F23]/80 border border-white/10 backdrop-blur-xl shadow-2xl">
            <span className="text-[10px] font-mono uppercase text-text-secondary pl-3 pr-2 flex items-center gap-1.5 font-semibold">
              <Sparkles className="size-3 text-primary animate-pulse" /> Live Simulation:
            </span>
            <button
              onClick={() => setActiveHeroScenario("safe")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
                activeHeroScenario === "safe"
                  ? "bg-primary text-bg-sunken font-bold shadow-[0_0_15px_rgba(0,255,255,0.4)]"
                  : "text-text-secondary hover:text-foreground hover:bg-white/5"
              }`}
            >
              Safe Trip Window
            </button>
            <button
              onClick={() => setActiveHeroScenario("conflict")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
                activeHeroScenario === "conflict"
                  ? "bg-warning text-bg-sunken font-bold shadow-[0_0_15px_rgba(255,176,32,0.4)]"
                  : "text-warning/80 hover:text-warning hover:bg-white/5"
              }`}
            >
              ⚡ Contradiction Check
            </button>
          </div>
        </div>

        {/* Cinematic 3-Panel Stage */}
        <div className="relative flex items-center justify-center min-h-[560px] md:min-h-[640px] overflow-hidden lg:overflow-visible">
          
          {/* ── LEFT PERIPHERAL SUPPORT PANEL (Enters from left edge) ── */}
          <motion.div
            initial={{ opacity: 0, x: -60 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hidden xl:flex flex-col gap-3 absolute -left-12 lg:-left-6 top-12 bottom-12 w-64 rounded-3xl border border-white/10 bg-[#080F23]/70 backdrop-blur-2xl p-5 shadow-2xl z-10 select-none pointer-events-none"
            style={{
              transform: "perspective(1000px) rotateY(12deg) translateZ(-30px)",
              maskImage: "linear-gradient(to right, transparent 0%, black 25%, black 100%)",
            }}
          >
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Activity className="size-3.5 text-primary" />
                <span className="text-[11px] font-heading font-bold uppercase tracking-wider text-white">
                  Marine Telemetry
                </span>
              </div>
              <span className="size-2 rounded-full bg-success animate-pulse" />
            </div>

            <div className="space-y-2.5 font-mono text-[11px]">
              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-[9px] uppercase text-text-secondary block">Sea Surface Temp</span>
                <span className="text-sm font-bold text-primary">28.4°C</span>
                <span className="text-[9px] text-text-secondary block mt-0.5">MOSDAC Altimetry Pass</span>
              </div>

              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-[9px] uppercase text-text-secondary block">Significant Wave</span>
                <span className="text-sm font-bold text-foreground">
                  {activeHeroScenario === "safe" ? "1.1m (Period 7.8s)" : "2.8m (Swell 11.4s)"}
                </span>
                <span className="text-[9px] text-text-secondary block mt-0.5">INCOIS Buoy #AD04</span>
              </div>

              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-[9px] uppercase text-text-secondary block">Coastal Wind</span>
                <span className="text-sm font-bold text-foreground">12 kts WSW</span>
                <span className="text-[9px] text-text-secondary block mt-0.5">IMD Mangalore Doppler</span>
              </div>

              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-[9px] uppercase text-text-secondary block">Current Vector</span>
                <span className="text-sm font-bold text-primary">0.8 kts SSE</span>
                <span className="text-[9px] text-text-secondary block mt-0.5">Tidal Drift Vector</span>
              </div>
            </div>
          </motion.div>

          {/* ── DOMINANT CENTRAL OCEAN INTELLIGENCE VIEWPORT ── */}
          <motion.div
            initial={{ opacity: 0, scale: 0.94, y: 30 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.1 }}
            className="w-full max-w-5xl rounded-3xl border border-white/15 bg-[#080F23]/80 backdrop-blur-2xl shadow-[0_0_100px_rgba(0,0,0,0.8)] relative overflow-hidden flex flex-col z-20"
          >
            {/* Ambient inner viewport glow */}
            <div 
              aria-hidden
              className="pointer-events-none absolute -top-28 -right-28 w-96 h-96 rounded-full bg-primary/20 blur-[100px]"
            />
            <div 
              aria-hidden
              className="pointer-events-none absolute -bottom-28 -left-28 w-96 h-96 rounded-full bg-accent-blue/30 blur-[100px]"
            />

            {/* Top Viewport Header HUD */}
            <div className="flex items-center justify-between px-6 py-3.5 border-b border-white/10 bg-black/30 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary shadow-[0_0_8px_#00FFFF]" />
                </span>
                <span className="text-xs font-heading font-bold uppercase tracking-wider text-white">
                  Sagarvani Ocean Intelligence Viewport
                </span>
                <span className="hidden sm:inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-primary/10 border border-primary/20 text-primary">
                  SECTOR: 12.91°N, 74.85°E · ARABIAN SEA
                </span>
              </div>

              <div className="flex items-center gap-3 text-[11px] font-mono text-text-secondary">
                <span className="flex items-center gap-1">
                  <Globe className="size-3 text-primary" /> Indian EEZ
                </span>
                <span className="hidden md:inline-block">INCOIS + IMD + ISRO</span>
              </div>
            </div>

            {/* Main Central Visual Surface (Cinematic Satellite/Earth Map Surface) */}
            <div className="relative w-full h-[400px] md:h-[480px] bg-gradient-to-b from-[#04081E] via-[#02051C] to-[#04081E] overflow-hidden flex items-center justify-center p-4 md:p-8">
              
              {/* Geospatial Coordinate Grid Lines */}
              <div className="absolute inset-0 opacity-25 bg-[linear-gradient(to_right,#1B2A6B_1px,transparent_1px),linear-gradient(to_bottom,#1B2A6B_1px,transparent_1px)] bg-[size:32px_32px]" />
              
              {/* Coastline & Bathymetric Contour Visual Layer */}
              <svg viewBox="0 0 800 450" className="absolute inset-0 w-full h-full opacity-75 preserve-3d" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="ocean-flow-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#00FFFF" stopOpacity="0.8" />
                    <stop offset="50%" stopColor="#38BDF8" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#0000FF" stopOpacity="0.1" />
                  </linearGradient>
                  <radialGradient id="radar-glow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#00FFFF" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#00FFFF" stopOpacity="0" />
                  </radialGradient>
                </defs>

                {/* Bathymetric depth shelf contours */}
                <path d="M 680 0 C 640 120, 660 280, 710 450" fill="none" stroke="#1B2A6B" strokeWidth="2.5" />
                <path d="M 590 0 C 540 140, 570 290, 620 450" fill="none" stroke="#1B2A6B" strokeWidth="1.5" strokeDasharray="6, 6" opacity="0.6" />
                <path d="M 460 0 C 410 160, 440 310, 500 450" fill="none" stroke="#00FFFF" strokeWidth="1" strokeDasharray="3, 5" opacity="0.25" />
                
                {/* Coastal Transit Safety Corridor */}
                <path d="M 220 280 Q 420 180 620 220" fill="none" stroke="url(#ocean-flow-grad)" strokeWidth="2.5" strokeDasharray="8, 6" />
                
                {/* Potential Fishing Zone (PFZ) Polygon */}
                <polygon points="340,140 480,110 510,180 370,210" fill="#22E29A" fillOpacity="0.12" stroke="#22E29A" strokeWidth="1.5" strokeDasharray="4, 4" />

                {/* Dynamic Swell Waves Vectors */}
                {activeHeroScenario === "conflict" && (
                  <circle cx="280" cy="220" r="90" fill="#FFB020" fillOpacity="0.1" stroke="#FFB020" strokeWidth="1.5" strokeDasharray="4, 6" />
                )}
              </svg>

              {/* Radar Pulse Rings */}
              <div className="absolute left-[38%] top-[45%] -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full border border-primary/20 animate-ping opacity-20 pointer-events-none" />
              <div className="absolute left-[38%] top-[45%] -translate-x-1/2 -translate-y-1/2 w-48 h-48 rounded-full border border-primary/35 pointer-events-none" />

              {/* Marine Markers & Reticles */}
              <div className="absolute top-12 left-10 md:left-24 flex items-center gap-2 bg-[#080F23]/85 border border-primary/40 px-2.5 py-1 rounded-lg shadow-lg font-mono text-[10px] text-primary backdrop-blur-md">
                <span className="size-2 rounded-full bg-primary animate-pulse" />
                <span>INCOIS Buoy #AD04: {activeHeroScenario === "safe" ? "1.1m Swell" : "2.8m High Swell"}</span>
              </div>

              <div className="absolute bottom-8 right-8 md:right-16 flex items-center gap-2 bg-[#080F23]/85 border border-white/15 px-2.5 py-1 rounded-lg shadow-lg font-mono text-[10px] text-text-secondary backdrop-blur-md">
                <MapPin className="size-3 text-primary" />
                <span>Mangalore Old Port (12.91°N, 74.85°E)</span>
              </div>

              {activeHeroScenario === "conflict" && (
                <div className="absolute bottom-20 left-12 md:left-28 flex items-center gap-2 bg-warning/15 border border-warning/50 px-3 py-1.5 rounded-xl shadow-xl font-mono text-[11px] text-warning backdrop-blur-md animate-pulse">
                  <AlertTriangle className="size-3.5" />
                  <span>Distant Pre-Monsoon Squall Line (60nm SW)</span>
                </div>
              )}

              {/* ── COMPACT FLOATING ORCA INTELLIGENCE CARD (Foreground Focus) ── */}
              <motion.div
                layout
                className="relative z-20 w-full max-w-xl rounded-2xl border border-white/15 bg-[#080F23]/90 p-5 md:p-6 shadow-[0_20px_50px_rgba(0,0,0,0.7)] backdrop-blur-2xl"
              >
                {/* User Query Banner */}
                <div className="flex items-center justify-between text-[11px] font-mono text-text-secondary mb-2.5">
                  <span className="flex items-center gap-1.5 text-primary font-bold">
                    <Radio className="size-3" /> ORCA INTENT SYNTHESIS
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-white/70">
                    Voice / Vernacular Input
                  </span>
                </div>

                <p className="text-xs md:text-sm font-medium text-white leading-relaxed italic mb-4">
                  {activeHeroScenario === "safe"
                    ? '"Is it safe for an 11-meter boat to fish 15 nautical miles off Mangalore Port tomorrow morning between 05:00 and 12:00?"'
                    : '"Local wind looks calm in Udupi, but radio mentions rough sea. Is it safe to head 25nm out for tuna today?"'
                  }
                </p>

                {/* 6 Specialists Micro-Telemetry Ribbon */}
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 mb-4 border-y border-white/10 py-2.5 font-mono text-[10px]">
                  {specialists.map((spec) => (
                    <div key={spec.name} className="flex flex-col items-center text-center p-1 rounded-lg bg-black/30">
                      <spec.icon className="size-3 text-primary mb-0.5" />
                      <span className="text-[9px] text-white/90 truncate w-full font-bold">{spec.name}</span>
                      <span className="text-[8px] text-text-secondary truncate w-full">
                        {activeHeroScenario === "conflict" && (spec.name === "Weather" || spec.name === "Marine Data") 
                          ? "Re-Checked" 
                          : spec.metric}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Validated Recommendation Result */}
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeHeroScenario}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className={`rounded-xl p-3.5 border ${
                      activeHeroScenario === "safe"
                        ? "bg-success/15 border-success/40 text-foreground"
                        : "bg-warning/15 border-warning/40 text-foreground"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                        activeHeroScenario === "safe" ? "text-success" : "text-warning"
                      }`}>
                        {activeHeroScenario === "safe" ? (
                          <>
                            <CheckCircle2 className="size-3.5" />
                            SAFE TO OPERATE — Favorable Window
                          </>
                        ) : (
                          <>
                            <AlertTriangle className="size-3.5" />
                            CAUTION ADVISED — Re-Checked Swell Hazard
                          </>
                        )}
                      </span>
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-black/40 text-white/80 font-bold border border-white/10">
                        {activeHeroScenario === "safe" ? "100% Consensus" : "Re-Check Reconciled"}
                      </span>
                    </div>
                    <p className="text-xs text-white/90 leading-relaxed">
                      {activeHeroScenario === "safe"
                        ? "Wave heights off Mangalore forecasted at 1.1m with calm 12 kts WSW winds. Safe 7-hour operating corridor confirmed within 18nm."
                        : "Do not proceed 25nm offshore. INCOIS buoys and MOSDAC altimetry confirm 2.8m long-period swell propagating from a distant squall line."
                      }
                    </p>
                  </motion.div>
                </AnimatePresence>
              </motion.div>

            </div>

            {/* Bottom Viewport Action Strip */}
            <div className="flex flex-wrap items-center justify-between px-6 py-3.5 border-t border-white/10 bg-black/30 backdrop-blur-md gap-3">
              <div className="flex items-center gap-2 text-[11px] font-mono text-text-secondary">
                <span className="size-2 rounded-full bg-success" />
                <span>Multi-Agent Consensus Layer: 100% Active</span>
              </div>
              <Button asChild size="sm" className="bg-primary text-bg-sunken font-bold hover:bg-primary/90 shadow-md">
                <Link href="/dashboard" className="flex items-center gap-1.5 text-xs">
                  <span>Launch Mission Console</span>
                  <ArrowRight className="size-3.5" />
                </Link>
              </Button>
            </div>
          </motion.div>

          {/* ── RIGHT PERIPHERAL SUPPORT PANEL (Enters from right edge) ── */}
          <motion.div
            initial={{ opacity: 0, x: 60 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hidden xl:flex flex-col gap-3 absolute -right-12 lg:-right-6 top-12 bottom-12 w-64 rounded-3xl border border-white/10 bg-[#080F23]/70 backdrop-blur-2xl p-5 shadow-2xl z-10 select-none pointer-events-none"
            style={{
              transform: "perspective(1000px) rotateY(-12deg) translateZ(-30px)",
              maskImage: "linear-gradient(to left, transparent 0%, black 25%, black 100%)",
            }}
          >
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-3.5 text-primary" />
                <span className="text-[11px] font-heading font-bold uppercase tracking-wider text-white">
                  Consensus Gate
                </span>
              </div>
              <span className="text-[9px] font-mono text-success font-bold">VERIFIED</span>
            </div>

            <div className="space-y-2.5 font-mono text-[11px]">
              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-[9px] uppercase text-text-secondary block">Active Specialists</span>
                <span className="text-sm font-bold text-foreground">6 / 6 Connected</span>
                <span className="text-[9px] text-primary block mt-0.5">Zero Single-Point Hallucination</span>
              </div>

              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-[9px] uppercase text-text-secondary block">Contradiction Engine</span>
                <span className={`text-sm font-bold ${activeHeroScenario === "safe" ? "text-success" : "text-warning"}`}>
                  {activeHeroScenario === "safe" ? "0 Conflicts" : "Re-Check Reconciled"}
                </span>
                <span className="text-[9px] text-text-secondary block mt-0.5">Satellite Cross-Comparison</span>
              </div>

              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-[9px] uppercase text-text-secondary block">Spatial Buffering</span>
                <span className="text-sm font-bold text-foreground">18nm Return Path</span>
                <span className="text-[9px] text-text-secondary block mt-0.5">ISRO Bhuvan Elevation</span>
              </div>

              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5">
                <span className="text-[9px] uppercase text-text-secondary block">Evidence Provenance</span>
                <span className="text-sm font-bold text-primary">100% Traceable</span>
                <span className="text-[9px] text-text-secondary block mt-0.5">MoES / IMD / ISRO</span>
              </div>
            </div>
          </motion.div>

        </div>
      </div>

      {/* Powered-by / Data Source Marquee */}
      <div className="mt-14 w-full max-w-4xl overflow-hidden">
        <p className="mb-3 text-center text-xs font-semibold uppercase tracking-widest text-text-secondary/70">
          Integrated with Official Marine & Geospatial Feeds
        </p>
        <div className="flex w-[200%] animate-marquee py-2.5 border-y border-border/40 bg-bg-sunken/40 backdrop-blur-sm rounded-xl">
          {["INCOIS (MoES)", "IMD Weather", "ISRO Bhuvan / NRSC", "Bhoonidhi", "MOSDAC Satellites", "BHASHINI + Sarvam AI", "Copernicus Marine"].map(
            (logo, i) => (
              <span
                key={`a-${i}`}
                className="mr-12 whitespace-nowrap font-heading text-xs font-bold uppercase tracking-wider text-text-secondary hover:text-primary transition-colors"
              >
                {logo}
              </span>
            )
          )}
          {["INCOIS (MoES)", "IMD Weather", "ISRO Bhuvan / NRSC", "Bhoonidhi", "MOSDAC Satellites", "BHASHINI + Sarvam AI", "Copernicus Marine"].map(
            (logo, i) => (
              <span
                key={`b-${i}`}
                className="mr-12 whitespace-nowrap font-heading text-xs font-bold uppercase tracking-wider text-text-secondary hover:text-primary transition-colors"
              >
                {logo}
              </span>
            )
          )}
        </div>
      </div>
    </WebGLLiquid>
  );
}
