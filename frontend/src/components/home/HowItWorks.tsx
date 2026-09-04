"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Network, ShieldCheck, CheckCircle2, ArrowRight, Sparkles, RefreshCw } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const tabs = [
  {
    id: "understand",
    label: "Understand",
    icon: MessageSquare,
    stageNum: "01",
    title: "Multilingual Intent & Context Interpretation",
    description: "Sagarvani understands natural language spoken queries in regional languages (Kannada, Hindi, Tamil, Telugu, etc.) or typed questions. It extracts location, vessel size, trip duration, and specific operational constraints.",
    tags: ["Intent Parsing", "Entity Extraction", "Vernacular Speech (BHASHINI)", "Vessel Profiling"],
    visual: {
      header: "Intent Extraction Pipeline",
      input: '"Kannada: ಮಂಗಳೂರು ಸಮೀಪ ನಾಳೆ ಬೆಳಿಗ್ಗೆ ಬೋಟು ತೆಗೆದುಕೊಂಡು ಹೋಗಬಹುದಾ?"',
      parsed: {
        location: "Mangalore Coast [12.91°N, 74.85°E]",
        temporalWindow: "Tomorrow 05:00 - 12:00 IST",
        vesselClass: "Small Motorized Craft (<12m)",
        requiredAgents: ["Marine Data", "Weather", "GIS", "Risk"]
      }
    }
  },
  {
    id: "orchestrate",
    label: "Orchestrate",
    icon: Network,
    stageNum: "02",
    title: "Parallel Multi-Agent Collaboration",
    description: "ORCA dispatches specialized agents in parallel. Rather than a monolithic LLM guessing at ocean physics, each specialist accesses authoritative feeds: INCOIS wave buoys, IMD radar, ISRO Bhuvan satellite imagery, and MOSDAC altimetry.",
    tags: ["Parallel Agent Execution", "INCOIS Feeds", "IMD Doppler", "ISRO Bhuvan GIS", "Spatial Buffers"],
    visual: {
      header: "ORCA Agent Dispatch Matrix",
      agents: [
        { name: "Marine Data Agent", task: "INCOIS Buoy #AD04 Significant Wave: 1.1m, Peak Period: 7.8s" },
        { name: "Weather Agent", task: "IMD Coastal Doppler: Wind 12 kts WSW, Zero squalls" },
        { name: "GIS Agent", task: "ISRO Bhuvan: 15nm offshore within Karnataka EEZ corridor" },
        { name: "Risk Agent", task: "Vessel stability envelope checked: Risk index LOW" }
      ]
    }
  },
  {
    id: "validate",
    label: "Validate",
    icon: ShieldCheck,
    stageNum: "03",
    title: "Contradiction Detection & Re-Planning",
    description: "Before rendering the final answer, ORCA cross-checks agent findings against each other. If there is a disagreement (e.g., calm shore wind vs high offshore swell), a visible re-check is triggered to reconcile evidence before giving a validated recommendation.",
    tags: ["Cross-Check Logic", "Contradiction Re-planning", "Evidence Provenance", "Uncertainty Transparency"],
    visual: {
      header: "Consensus & Validation Gate",
      status: "VALIDATED WITH HIGH CONFIDENCE",
      checks: [
        { check: "Wave height verified across INCOIS Buoy & Forecast", passed: true },
        { check: "Wind vector corroborated between IMD & Surface Radar", passed: true },
        { check: "Zero navigational or squall hazards in 18nm buffer", passed: true }
      ],
      output: "SAFE TO OPERATE — 7-hour stable window identified."
    }
  },
];

export function HowItWorks() {
  const [activeTab, setActiveTab] = useState(tabs[0].id);
  const activeContent = tabs.find((t) => t.id === activeTab)!;

  return (
    <section id="how-it-works" className="py-24 md:py-32 px-6 lg:px-12 bg-bg-sunken border-b border-border relative overflow-hidden">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16 max-w-3xl mx-auto">
          <span className="text-primary text-xs font-heading font-bold uppercase tracking-widest bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
            Pipeline Architecture
          </span>
          <h2 className="font-heading font-bold text-3xl md:text-5xl text-foreground mt-4">
            How Sagarvani Works
          </h2>
          <p className="mt-4 text-text-secondary text-base leading-relaxed">
            From natural language question to validated recommendation. ORCA ensures no answer is rendered without cross-checked multi-source evidence.
          </p>
        </div>

        {/* Tab Selection Surface */}
        <div className="flex justify-center mb-12">
          <div className="inline-flex p-1.5 rounded-2xl bg-bg-elevated border border-border gap-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2.5 px-6 py-3 rounded-xl font-heading text-sm font-semibold transition-all duration-200 ${
                    isActive
                      ? "bg-primary text-bg-sunken shadow-[0_0_20px_rgba(0,255,255,0.25)]"
                      : "text-text-secondary hover:text-foreground hover:bg-bg-primary/50"
                  }`}
                >
                  <Icon className="size-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content Canvas */}
        <div className="bg-bg-elevated/70 border border-border rounded-3xl p-8 md:p-12 shadow-2xl relative overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.35 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center"
            >
              {/* Left Column: Description & Tags */}
              <div className="lg:col-span-6 flex flex-col justify-center">
                <div className="flex items-center gap-3 mb-4">
                  <span className="font-mono text-xs font-bold text-primary px-2.5 py-1 rounded bg-bg-sunken border border-border">
                    STAGE {activeContent.stageNum}
                  </span>
                  <span className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
                    ORCA Pipeline
                  </span>
                </div>
                <h3 className="font-heading font-bold text-2xl md:text-3xl text-foreground mb-4">
                  {activeContent.title}
                </h3>
                <p className="text-text-secondary text-base leading-relaxed mb-8">
                  {activeContent.description}
                </p>

                <div className="flex flex-wrap gap-2 mb-8">
                  {activeContent.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-3 py-1 rounded-lg bg-bg-sunken border border-border text-xs font-mono text-text-secondary"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="flex items-center gap-4">
                  <Button asChild className="bg-primary text-bg-sunken font-bold hover:bg-primary/90">
                    <Link href="/dashboard" className="flex items-center gap-2">
                      <span>Experience in Console</span>
                      <ArrowRight className="size-4" />
                    </Link>
                  </Button>
                </div>
              </div>

              {/* Right Column: Visual Stage Simulation */}
              <div className="lg:col-span-6">
                <div className="rounded-2xl border border-border bg-bg-sunken p-6 shadow-inner font-mono text-xs">
                  <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
                    <span className="text-primary font-bold uppercase tracking-wider text-[11px]">
                      {activeContent.visual.header}
                    </span>
                    <span className="size-2 rounded-full bg-primary animate-pulse" />
                  </div>

                  {activeTab === "understand" && (
                    <div className="space-y-4">
                      <div className="p-3 rounded-lg bg-bg-elevated border border-border/80 text-foreground">
                        <span className="text-[10px] uppercase text-text-secondary block mb-1">Raw Speech / Text Input</span>
                        <p className="italic text-text-primary text-xs">{(activeContent.visual as any).input}</p>
                      </div>
                      <div className="space-y-2 p-3 rounded-lg bg-bg-elevated/40 border border-border/50">
                        <span className="text-[10px] uppercase text-primary block font-bold">Structured Extracted Parameters</span>
                        <div className="grid grid-cols-2 gap-2 text-[11px]">
                          <div><span className="text-text-secondary">Target Location:</span> <span className="text-foreground">{(activeContent.visual as any).parsed.location}</span></div>
                          <div><span className="text-text-secondary">Time Window:</span> <span className="text-foreground">{(activeContent.visual as any).parsed.temporalWindow}</span></div>
                          <div><span className="text-text-secondary">Vessel Type:</span> <span className="text-foreground">{(activeContent.visual as any).parsed.vesselClass}</span></div>
                          <div><span className="text-text-secondary">Specialists:</span> <span className="text-primary font-bold">4 Dispatched</span></div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === "orchestrate" && (
                    <div className="space-y-2.5">
                      {(activeContent.visual as any).agents.map((agent: any, i: number) => (
                        <div key={i} className="p-2.5 rounded-lg bg-bg-elevated border border-border flex items-start justify-between gap-3">
                          <div className="flex flex-col">
                            <span className="font-bold text-primary text-[11px]">{agent.name}</span>
                            <span className="text-text-secondary text-[11px]">{agent.task}</span>
                          </div>
                          <span className="text-[10px] text-success font-bold shrink-0 mt-0.5">READY</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeTab === "validate" && (
                    <div className="space-y-3">
                      <div className="p-3 rounded-lg bg-success/10 border border-success/30 text-success flex items-center justify-between">
                        <span className="font-bold">{(activeContent.visual as any).status}</span>
                        <CheckCircle2 className="size-4" />
                      </div>
                      <div className="space-y-1.5">
                        {(activeContent.visual as any).checks.map((c: any, i: number) => (
                          <div key={i} className="flex items-center gap-2 text-text-secondary text-[11px]">
                            <CheckCircle2 className="size-3.5 text-success shrink-0" />
                            <span>{c.check}</span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 p-3 rounded-lg bg-bg-elevated border border-border">
                        <span className="text-[10px] text-text-secondary uppercase block mb-1">Synthesized Advisory</span>
                        <p className="text-foreground font-semibold text-xs">{(activeContent.visual as any).output}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
