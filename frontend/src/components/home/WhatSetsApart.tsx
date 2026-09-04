"use client";

import { motion } from "framer-motion";
import { Network, RefreshCw, FileCheck, Globe, Phone, RadioTower } from "lucide-react";

const features = [
  {
    title: "Multi-Agent Intelligence",
    icon: Network,
    desc: "Six specialized agents fuse ocean, weather, and geospatial data instead of leaving users to interpret fragmented information manually.",
    badge: "Parallel Collaboration",
  },
  {
    title: "Re-planning on Contradictions",
    icon: RefreshCw,
    desc: "When sources conflict or confidence is low, the reasoning and validation layer re-checks and re-analyzes before the answer is presented.",
    badge: "Active Verification",
  },
  {
    title: "Explainable Recommendations",
    icon: FileCheck,
    desc: "Recommendations come with evidence-backed reasoning so users can understand why a result was produced.",
    badge: "100% Provenance",
  },
];

const accessPaths = [
  { 
    title: "Web / App Console", 
    icon: Globe, 
    desc: "Interactive spatial map, multi-agent status rails, and high-resolution layer analytics for researchers and maritime operators." 
  },
  { 
    title: "Voice Helpline / IVR", 
    icon: Phone, 
    desc: "Dial-in conversational queries in regional languages, delivering concise verbal advisories to fishermen without smartphones." 
  },
  { 
    title: "Low-Bandwidth Portal", 
    icon: RadioTower, 
    desc: "Lightweight, compressed text and spatial payloads designed to operate reliably over constrained 2G/coastal radio networks." 
  },
];

export function WhatSetsApart() {
  return (
    <section id="solutions" className="py-24 md:py-32 border-b border-border bg-bg-primary relative overflow-hidden">
      {/* Subtle ambient light */}
      <div 
        aria-hidden 
        className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[800px] h-[350px] bg-primary/5 blur-[120px] rounded-full"
      />

      <div className="max-w-7xl mx-auto px-6 lg:px-12 relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16 max-w-3xl mx-auto"
        >
          <span className="text-primary text-xs font-heading font-bold uppercase tracking-widest bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
            Core Differentiation
          </span>
          <h2 className="font-heading font-bold text-3xl md:text-5xl text-foreground mt-4">
            What sets Sagarvani apart.
          </h2>
          <p className="mt-4 text-text-secondary text-base leading-relaxed">
            Unlike isolated dashboards or generic chat interfaces, Sagarvani is an active marine reasoning engine designed for operational trust.
          </p>
        </motion.div>

        {/* 3 Core Differentiation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="group p-8 rounded-2xl border border-border bg-bg-elevated/70 hover:bg-bg-elevated hover:border-primary/50 transition-all duration-300 flex flex-col justify-between shadow-[0_0_30px_rgba(0,0,0,0.2)]"
            >
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                    <f.icon size={26} strokeWidth={1.75} />
                  </div>
                  <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-primary px-2.5 py-1 rounded bg-bg-sunken border border-border">
                    {f.badge}
                  </span>
                </div>
                <h3 className="font-heading font-bold text-xl text-foreground mb-3">{f.title}</h3>
                <p className="text-text-secondary text-sm leading-relaxed">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Supporting Highlight: One Intelligence Engine, Three Access Paths */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="rounded-2xl border border-border bg-bg-sunken p-8 md:p-12 shadow-2xl relative overflow-hidden"
        >
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10 border-b border-border/80 pb-6">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-widest text-primary font-bold">
                Omnichannel Architecture
              </span>
              <h3 className="font-heading font-bold text-2xl md:text-3xl text-foreground mt-1">
                One Intelligence Engine, Three Access Paths
              </h3>
            </div>
            <span className="text-xs text-text-secondary font-mono px-3 py-1 rounded-full bg-bg-elevated border border-border">
              Common ORCA Core
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {accessPaths.map((path) => (
              <div key={path.title} className="flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-bg-elevated border border-border flex items-center justify-center text-primary">
                    <path.icon size={18} />
                  </div>
                  <h4 className="font-heading font-semibold text-base text-foreground">{path.title}</h4>
                </div>
                <p className="text-xs leading-relaxed text-text-secondary">{path.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
