"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  CheckCircle2, 
  RefreshCw, 
  ShieldCheck, 
  AlertTriangle, 
  ArrowRight, 
  Layers, 
  Cpu, 
  GitCompare,
  FileCheck,
  Sparkles
} from "lucide-react";

const pillars = [
  {
    label: "Continuous Multi-Source Validation",
    icon: CheckCircle2,
    desc: "Every feed (INCOIS buoys, IMD radar, ISRO Bhuvan) is validated for sensor quality, latency, and spatial relevance before ingestion.",
    badge: "Layer 1: Input Integrity"
  },
  {
    label: "Source Diversity & Fallbacks",
    icon: RefreshCw,
    desc: "If a satellite pass is clouded or a buoy is offline, ORCA switches to secondary numerical models automatically — with degraded confidence flagged clearly.",
    badge: "Layer 2: Fallback Diversity"
  },
  {
    label: "Active Re-Planning on Contradiction",
    icon: ShieldCheck,
    desc: "When weather forecasts conflict with ocean swell observations, ORCA halts immediate output and executes a secondary verification pass before answering.",
    badge: "Layer 3: Conflict Reconciliation"
  },
];

const pipelineSteps = [
  {
    id: "sources",
    label: "1. SOURCE INPUTS",
    state: "RUNNING",
    stateColor: "text-primary border-primary/30 bg-primary/10",
    desc: "Ingesting INCOIS Buoy #AD04, IMD Coastal Radar, and MOSDAC Altimetry.",
    signal: "3 Active Feeds"
  },
  {
    id: "agents",
    label: "2. AGENT OUTPUTS",
    state: "CONFLICT",
    stateColor: "text-warning border-warning/30 bg-warning/10",
    desc: "Weather Agent reports calm shore wind (7 kts), but Marine Data Agent detects 2.8m long-period swell.",
    signal: "Discrepancy Found"
  },
  {
    id: "crosscheck",
    label: "3. CROSS-CHECK",
    state: "RE-CHECKING",
    stateColor: "text-warning border-warning/30 bg-warning/10",
    desc: "ORCA triggers Re-Planning: Fetching offshore satellite altimetry to evaluate swell propagation.",
    signal: "Re-Plan Active"
  },
  {
    id: "validated",
    label: "4. VALIDATED RESULT",
    state: "VALIDATED",
    stateColor: "text-success border-success/30 bg-success/10",
    desc: "Confirmed distant squall generating swell without shore wind. Caution advisory issued with full citation trace.",
    signal: "High Confidence"
  }
];

export function Reliability() {
  const [activeStep, setActiveStep] = useState(1);

  return (
    <section className="py-24 md:py-32 border-b border-border bg-bg-primary relative overflow-hidden">
      {/* Glow background */}
      <div 
        aria-hidden 
        className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-primary/5 blur-[100px] rounded-full"
      />

      <div className="max-w-7xl mx-auto px-6 lg:px-12 relative z-10">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16 max-w-3xl mx-auto"
        >
          <span className="text-primary text-xs font-heading font-bold uppercase tracking-widest bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
            Reliability & Trust
          </span>
          <h2 className="font-heading font-bold text-3xl md:text-5xl text-foreground mt-4">
            Answers you can trust, by design.
          </h2>
          <p className="mt-4 text-text-secondary text-base leading-relaxed">
            Sagarvani does not silently guess when data sources disagree. ORCA detects contradictions, initiates re-checking, and exposes the exact validation trace.
          </p>
        </motion.div>

        {/* Dynamic Contradiction & Re-Planning Interactive Showcase */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="rounded-3xl border border-border bg-bg-sunken p-8 md:p-12 shadow-2xl mb-16"
        >
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 border-b border-border pb-6">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-primary font-bold">
                Live Contradiction Resolution Protocol
              </span>
              <h3 className="font-heading font-bold text-2xl text-foreground mt-1">
                How ORCA Resolves Conflicting Signals
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-secondary font-mono">Interactive Stage:</span>
              <div className="flex gap-1.5">
                {pipelineSteps.map((step, idx) => (
                  <button
                    key={step.id}
                    onClick={() => setActiveStep(idx)}
                    className={`w-7 h-7 rounded-lg font-mono text-xs font-bold transition-all ${
                      activeStep === idx 
                        ? "bg-primary text-bg-sunken shadow-[0_0_10px_rgba(0,255,255,0.4)]" 
                        : "bg-bg-elevated border border-border text-text-secondary hover:text-foreground"
                    }`}
                  >
                    0{idx + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 4 Pipeline Sequence Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {pipelineSteps.map((step, idx) => {
              const isActive = activeStep === idx;
              return (
                <div
                  key={step.id}
                  onClick={() => setActiveStep(idx)}
                  className={`cursor-pointer rounded-2xl border p-5 transition-all duration-200 flex flex-col justify-between ${
                    isActive
                      ? "border-primary bg-bg-elevated shadow-[0_0_24px_rgba(0,255,255,0.08)] scale-[1.02]"
                      : "border-border bg-bg-elevated/40 hover:bg-bg-elevated/70"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-mono text-[11px] font-bold text-text-secondary">
                        {step.label}
                      </span>
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${step.stateColor}`}>
                        {step.state}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary leading-relaxed">
                      {step.desc}
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-border/50 flex items-center justify-between text-[10px] font-mono text-primary font-semibold">
                    <span>{step.signal}</span>
                    <ArrowRight className="size-3" />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Active Step Deep-Dive Box */}
          <div className="p-6 rounded-2xl bg-bg-elevated/60 border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
                <GitCompare size={24} />
              </div>
              <div>
                <h4 className="font-heading font-semibold text-base text-foreground">
                  Current Pipeline State: {pipelineSteps[activeStep].label}
                </h4>
                <p className="text-xs text-text-secondary mt-0.5">
                  {pipelineSteps[activeStep].desc}
                </p>
              </div>
            </div>
            <div className="shrink-0 flex items-center gap-2">
              <span className="text-xs text-text-secondary font-mono">System Confidence:</span>
              <span className="text-xs font-mono font-bold text-success px-2.5 py-1 rounded bg-success/15 border border-success/30">
                {activeStep === 3 ? "Validated (High)" : activeStep === 1 ? "Conflict Flagged" : "Evaluating Feeds"}
              </span>
            </div>
          </div>
        </motion.div>

        {/* 3 Core Reliability Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pillars.map((p, i) => (
            <motion.div
              key={p.label}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="p-8 rounded-2xl border border-border bg-bg-elevated/70 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <p.icon className="text-success" size={28} strokeWidth={1.75} />
                  <span className="text-[10px] font-mono text-text-secondary px-2 py-0.5 rounded bg-bg-sunken border border-border">
                    {p.badge}
                  </span>
                </div>
                <h3 className="font-heading font-semibold text-lg text-foreground mb-3">{p.label}</h3>
                <p className="text-text-secondary text-sm leading-relaxed">{p.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
