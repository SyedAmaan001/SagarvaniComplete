"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Anchor,
  Navigation,
  LineChart,
  ShieldAlert,
  Fish,
  Sun,
  Flame,
  Globe2,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

interface Stakeholder {
  id: string;
  title: string;
  role: string;
  icon: React.ElementType;
  badge: string;
  desc: string;
  cardTitle: string;
  cardSubtitle: string;
  cardDesc: string;
  bgColor: string;
  accentColor: string;
  textColor: string;
  stats: { label: string; value: string }[];
  features: string[];
}

const STAKEHOLDERS: Stakeholder[] = [
  {
    id: "fishermen",
    title: "Fishermen & Coastal Crews",
    role: "Operational Safety & PFZ",
    icon: Anchor,
    badge: "Voice & Low-Bandwidth",
    desc: "Voice-based advisories about safe fishing windows, wave height thresholds, and Potential Fishing Zones delivered in regional languages over IVR or helpline.",
    cardTitle: "Pre-Departure Safety & PFZ Mapping",
    cardSubtitle: "Natural language advisories for artisanal & mechanized crews",
    cardDesc:
      "Consolidated trip guidance validated across INCOIS wave buoys, IMD Doppler weather radar, and vessel risk thresholds before departure.",
    bgColor: "#0B1550",
    accentColor: "#00FFFF",
    textColor: "#F4F7FF",
    stats: [
      { label: "Primary Feeds", value: "INCOIS + IMD" },
      { label: "Access Paths", value: "Voice / Helpline / Web" },
    ],
    features: [
      "Potential Fishing Zone (PFZ) coordinate mapping",
      "Wave height & localized squall hazard thresholds",
      "Vernacular audio alerts (Kannada, Tamil, Hindi, Telugu)",
    ],
  },
  {
    id: "operators",
    title: "Marine & Port Operators",
    role: "Fleet Routing & Operations",
    icon: Navigation,
    badge: "Live GIS Matrix",
    desc: "Interactive GIS console with weather routing, tidal currents, bathymetric depths, and multi-agent risk synthesis.",
    cardTitle: "Coastal Transit & Port Approach",
    cardSubtitle: "Dynamic weather routing & spatial hazard buffers",
    cardDesc:
      "High-resolution spatial overlays with dynamic hazard zones, sea surface temperature gradients, and harbour clearance intelligence.",
    bgColor: "#050A30",
    accentColor: "#38BDF8",
    textColor: "#F4F7FF",
    stats: [
      { label: "Data Resolution", value: "Coastal & EEZ" },
      { label: "Key Parameters", value: "Swell + Current Vectors" },
    ],
    features: [
      "Dynamic weather-optimised route calculation",
      "Port approach & anchor depth constraints",
      "Live INCOIS wave spectrum integration",
    ],
  },
  {
    id: "researchers",
    title: "Ocean Researchers & Scientists",
    role: "Multi-Source Exploration",
    icon: LineChart,
    badge: "Analytical Synthesis",
    desc: "Unified exploration across INCOIS, IMD, ISRO Bhuvan, and MOSDAC with anomaly detection and verifiable citation trails.",
    cardTitle: "Ocean Data Synthesis & Anomaly Detection",
    cardSubtitle: "Multi-satellite correlation & spatial indicators",
    cardDesc:
      "Historical trend analysis, salinity & temperature anomaly clustering, and exportable research-grade citations for marine science.",
    bgColor: "#02051C",
    accentColor: "#A78BFA",
    textColor: "#F4F7FF",
    stats: [
      { label: "Integrated Feeds", value: "MOSDAC + Bhoonidhi" },
      { label: "Citation Model", value: "Verifiable Source Provenance" },
    ],
    features: [
      "Multi-modal cross-sensor contradiction checks",
      "ISRO Bhuvan & MOSDAC spatial layers",
      "Exportable data reports with provenance logs",
    ],
  },
  {
    id: "disaster",
    title: "Disaster Management & Safety",
    role: "Hazard Early Warning",
    icon: ShieldAlert,
    badge: "Surge & Cyclone Context",
    desc: "Harmonized emergency picture combining IMD cyclone paths, INCOIS coastal surge models, and vulnerable coastal zone mappings.",
    cardTitle: "Coastal Hazard Mitigation & Surge Context",
    cardSubtitle: "Multi-agency emergency spatial awareness",
    cardDesc:
      "Rapid decision support fusing conflicting weather advisories into one transparent operational risk picture for coastal relief coordinators.",
    bgColor: "#091238",
    accentColor: "#FFB020",
    textColor: "#F4F7FF",
    stats: [
      { label: "Hazard Focus", value: "Cyclones & High Waves" },
      { label: "Conflict State", value: "Visible Re-Checking" },
    ],
    features: [
      "Cross-agency contradiction detection",
      "Coastal inundation & high-swell alerts",
      "Evacuation corridor spatial reasoning",
    ],
  },
  {
    id: "aquaculture",
    title: "Aquaculture & Marine Farming",
    role: "Environmental Monitoring",
    icon: Fish,
    badge: "Water & Bio-Signals",
    desc: "Connect farm decisions to localized water quality, temperature anomalies, and algal bloom risk indicators.",
    cardTitle: "Hatchery & Coastal Farm Protection",
    cardSubtitle: "Water temperature & environmental stability",
    cardDesc:
      "Real-time monitoring of sea-surface temperature changes and coastal run-off patterns to protect marine hatchery operations.",
    bgColor: "#061A40",
    accentColor: "#22E29A",
    textColor: "#F4F7FF",
    stats: [
      { label: "Signals Tracked", value: "SST + Chlorophyll-a" },
      { label: "Threshold Alerts", value: "Thermal Stress & Upwelling" },
    ],
    features: [
      "Localized thermal stress indicators",
      "Near-shore salinity fluctuation alerts",
      "Seasonal upwelling forecast windows",
    ],
  },
  {
    id: "tourism",
    title: "Coastal Tourism & Recreation",
    role: "Activity Window Planning",
    icon: Sun,
    badge: "Sea-State Safety",
    desc: "Plan coastal recreation, ferry transits, and water-sports around verified wave, rip-current, and wind conditions.",
    cardTitle: "Recreational Coastal & Ferry Safety",
    cardSubtitle: "Tourist vessel & coastal activity windows",
    cardDesc:
      "Accurate sea-state advisories preventing tourist boat accidents during sudden pre-monsoon squall developments.",
    bgColor: "#0A174E",
    accentColor: "#F59E0B",
    textColor: "#F4F7FF",
    stats: [
      { label: "Safety Windows", value: "Hourly Temporal Forecast" },
      { label: "Hazards Mapped", value: "Rip Currents & High Swells" },
    ],
    features: [
      "Safe bathing & boating window forecast",
      "Ferry route swell & chop advisory",
      "Beachfront weather trend summaries",
    ],
  },
  {
    id: "offshore",
    title: "Offshore Energy & Marine Industry",
    role: "Platform Operations",
    icon: Flame,
    badge: "Asset & Logistics Context",
    desc: "Ocean current, wind shear, and wave spectrum analysis for offshore platforms, maintenance barges, and subsea operations.",
    cardTitle: "Offshore Industrial Intelligence",
    cardSubtitle: "Platform operations & heavy lift windows",
    cardDesc:
      "Comprehensive hydrodynamic forecasts and sub-surface current profiles to schedule crane barge operations and crew transfers safely.",
    bgColor: "#030A28",
    accentColor: "#EC4899",
    textColor: "#F4F7FF",
    stats: [
      { label: "Profile Depth", value: "Surface to Sub-Surface" },
      { label: "Operational State", value: "Validated Decision Support" },
    ],
    features: [
      "Significant wave height & peak period alerts",
      "Subsea current speed & direction modeling",
      "Helideck turbulence & visibility forecasts",
    ],
  },
  {
    id: "policy",
    title: "Marine Policy & Conservation",
    role: "Evidence Synthesis",
    icon: Globe2,
    badge: "Ecosystem Indicators",
    desc: "Synthesize multi-source satellite records, marine protected area boundaries, and ecological indicators for evidence-based governance.",
    cardTitle: "Marine Spatial Planning & Protection",
    cardSubtitle: "Evidence-based ocean governance",
    cardDesc:
      "Holistic environmental layers and maritime traffic density mappings supporting sustainable coastal zone management.",
    bgColor: "#02051C",
    accentColor: "#6366F1",
    textColor: "#F4F7FF",
    stats: [
      { label: "Spatial Feeds", value: "ISRO + INCOIS Layers" },
      { label: "Governance Output", value: "Structured Provenance" },
    ],
    features: [
      "Marine Protected Area (MPA) buffer monitoring",
      "Long-term SST & sea-level trend indicators",
      "Multi-disciplinary geospatial synthesis",
    ],
  },
];

export function SplitCardSection() {
  const [activeTab, setActiveTab] = useState<number>(0);
  const active = STAKEHOLDERS[activeTab];

  return (
    <section id="who-is-it-for" className="relative overflow-hidden border-b border-border bg-bg-primary py-24 md:py-32">
      {/* Background ambient lighting */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          background:
            "radial-gradient(ellipse at 80% 50%, rgba(0, 255, 255, 0.08) 0%, transparent 60%)",
        }}
      />

      <div className="relative z-10 mx-auto max-w-7xl px-6 lg:px-12">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
          className="mb-16 text-center"
        >
          <span className="text-primary text-xs font-heading font-bold uppercase tracking-widest bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
            WHO IS IT FOR
          </span>
          <h2 className="mt-4 font-heading text-3xl font-bold text-foreground md:text-5xl">
            Built for every ocean stakeholder.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-text-secondary text-base">
            Tailored decision intelligence whether you are steering a fishing trawler, managing a commercial fleet, responding to coastal hazards, or researching marine systems.
          </p>
        </motion.div>

        {/* 2-Column Responsive Layout */}
        <div className="grid grid-cols-1 items-start gap-10 lg:grid-cols-12 lg:gap-14">
          {/* Left Column: Stakeholder Selector */}
          <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 lg:col-span-5 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
            {STAKEHOLDERS.map((s, index) => {
              const Icon = s.icon;
              const isSelected = activeTab === index;
              return (
                <motion.div
                  key={s.id}
                  onClick={() => setActiveTab(index)}
                  initial={{ opacity: 0, x: -15 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: index * 0.04 }}
                  className={`group relative cursor-pointer rounded-xl border p-4 transition-all duration-200 ${
                    isSelected
                      ? "border-primary bg-bg-elevated shadow-[0_0_24px_rgba(0,255,255,0.08)]"
                      : "border-border bg-bg-elevated/40 hover:border-border/80 hover:bg-bg-elevated/70"
                  }`}
                >
                  <div className="flex items-start gap-3.5">
                    <div
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border transition-colors ${
                        isSelected
                          ? "border-primary/50 bg-primary/10 text-primary"
                          : "border-border bg-bg-primary text-text-secondary group-hover:text-primary"
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <h3 className="font-heading text-sm font-semibold text-foreground truncate">
                          {s.title}
                        </h3>
                        <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-[9px] font-semibold text-primary">
                          {s.badge}
                        </span>
                      </div>
                      <p className="mt-1 text-xs leading-relaxed text-text-secondary line-clamp-2">
                        {s.desc}
                      </p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Right Column: 3D Layered Detail Card */}
          <div className="relative flex items-center justify-center lg:col-span-7 lg:sticky lg:top-28">
            <div className="relative w-full max-w-xl">
              <AnimatePresence mode="wait">
                <motion.div
                  key={active.id}
                  initial={{ opacity: 0, y: 15, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -15, scale: 0.97 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="overflow-hidden rounded-2xl border border-border/80 p-7 md:p-8 shadow-2xl"
                  style={{
                    backgroundColor: active.bgColor,
                    boxShadow: `0 20px 50px -10px ${active.accentColor}18, 0 0 0 1px var(--color-border)`,
                  }}
                >
                  {/* Top Bar with Icon & Role */}
                  <div className="flex items-center justify-between border-b border-white/10 pb-4">
                    <div className="flex items-center gap-3">
                      <div
                        className="flex h-11 w-11 items-center justify-center rounded-xl"
                        style={{ backgroundColor: `${active.accentColor}20`, color: active.accentColor }}
                      >
                        <active.icon className="h-6 w-6" />
                      </div>
                      <div>
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-white/60">
                          {active.role}
                        </span>
                        <h4 className="font-heading text-xl font-bold text-white">
                          {active.cardTitle}
                        </h4>
                      </div>
                    </div>
                    <span
                      className="rounded-full px-3 py-1 font-mono text-xs font-bold"
                      style={{ backgroundColor: `${active.accentColor}22`, color: active.accentColor }}
                    >
                      {active.badge}
                    </span>
                  </div>

                  {/* Main Description */}
                  <div className="my-5">
                    <p className="text-sm font-semibold text-white/90">
                      {active.cardSubtitle}
                    </p>
                    <p className="mt-2 text-xs leading-relaxed text-white/70">
                      {active.cardDesc}
                    </p>
                  </div>

                  {/* Features List */}
                  <div className="space-y-2 rounded-xl border border-white/10 bg-black/25 p-4">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-white/50 block mb-1">
                      Validated Capabilities
                    </span>
                    {active.features.map((feat, i) => (
                      <div key={i} className="flex items-center gap-2.5 text-xs text-white/85">
                        <CheckCircle2 className="size-3.5 shrink-0" style={{ color: active.accentColor }} />
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>

                  {/* Bottom Stats & CTA */}
                  <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-white/10 pt-4">
                    <div className="flex gap-6">
                      {active.stats.map((st) => (
                        <div key={st.label}>
                          <span className="block font-heading text-sm font-bold" style={{ color: active.accentColor }}>
                            {st.value}
                          </span>
                          <span className="text-[10px] uppercase tracking-wider text-white/50">{st.label}</span>
                        </div>
                      ))}
                    </div>

                    <Button
                      asChild
                      size="sm"
                      className="font-semibold transition-transform hover:scale-105"
                      style={{
                        backgroundColor: active.accentColor,
                        color: "#02051C",
                      }}
                    >
                      <Link href="/dashboard" className="flex items-center gap-1.5 text-xs">
                        Launch in Console <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </Button>
                  </div>
                </motion.div>
              </AnimatePresence>

              {/* Decorative 3D background layer cards */}
              <div
                aria-hidden
                className="pointer-events-none absolute -bottom-3 -right-3 -z-10 h-full w-full rounded-2xl border border-white/5 bg-bg-sunken/60 backdrop-blur-sm"
                style={{ transform: "rotate(1.5deg)" }}
              />
              <div
                aria-hidden
                className="pointer-events-none absolute -bottom-6 -right-6 -z-20 h-full w-full rounded-2xl border border-white/5 bg-bg-sunken/30"
                style={{ transform: "rotate(3deg)" }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
