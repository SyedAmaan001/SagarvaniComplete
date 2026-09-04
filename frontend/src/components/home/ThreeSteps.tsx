"use client";

import { motion } from "framer-motion";
import { MessageSquare, Cpu, ShieldCheck, Waves, CloudRain, MapPin, CheckCircle2, ArrowRight } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export function ThreeSteps() {
  const steps = [
    {
      num: "01",
      title: "Ask",
      description:
        'Ask the marine question naturally — via text, voice, or helpline. "Is it safe for a 12-meter vessel to operate near Mangalore Port tomorrow morning?"',
      align: "left",
      visual: (
        <div className="w-full h-full flex flex-col justify-between p-6 bg-bg-sunken/90 rounded-xl border border-border">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <MessageSquare className="text-primary size-4" />
              <span className="text-xs font-semibold uppercase tracking-wider text-text-primary">Natural Language Query</span>
            </div>
            <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-mono">English / Hindi / Kannada</span>
          </div>
          <div className="my-4 bg-bg-elevated p-4 rounded-lg border border-border">
            <p className="text-sm text-text-primary font-medium italic">
              "Is it safe for a 12-meter vessel to operate near Mangalore Port tomorrow morning?"
            </p>
          </div>
          <div className="flex items-center justify-between text-xs text-text-secondary">
            <span className="flex items-center gap-1.5 text-success">
              <span className="size-2 rounded-full bg-success animate-pulse" />
              Voice / Text Received
            </span>
            <span className="font-mono text-[11px] text-primary">Location: 12.9141° N, 74.8560° E</span>
          </div>
        </div>
      ),
    },
    {
      num: "02",
      title: "Orchestrate",
      description:
        "ORCA coordinates the specialist agents and relevant data — dispatching marine, weather, GIS, analytics, risk, and spatial agents simultaneously.",
      align: "right",
      visual: (
        <div className="w-full h-full flex flex-col justify-between p-6 bg-bg-sunken/90 rounded-xl border border-border">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <Cpu className="text-primary size-4" />
              <span className="text-xs font-semibold uppercase tracking-wider text-text-primary">ORCA Dispatch Matrix</span>
            </div>
            <span className="text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded-full font-mono">6 Agents Active</span>
          </div>
          <div className="grid grid-cols-2 gap-2 my-2">
            {[
              { icon: Waves, label: "Marine Data", status: "Validated" },
              { icon: CloudRain, label: "Weather", status: "Validated" },
              { icon: MapPin, label: "GIS Spatial", status: "Validated" },
              { icon: ShieldCheck, label: "Risk Assessment", status: "Checking" },
            ].map((a) => (
              <div key={a.label} className="flex items-center justify-between bg-bg-elevated/80 p-2.5 rounded border border-border">
                <div className="flex items-center gap-2">
                  <a.icon className="size-3.5 text-primary" />
                  <span className="text-xs text-text-primary font-medium">{a.label}</span>
                </div>
                <span className="text-[10px] text-success font-semibold">{a.status}</span>
              </div>
            ))}
          </div>
          <div className="text-[11px] text-text-secondary flex justify-between items-center">
            <span>Synthesis Engine: ORCA Multi-Agent</span>
            <span className="text-primary font-mono">Latency: 1.2s</span>
          </div>
        </div>
      ),
    },
    {
      num: "03",
      title: "Validate",
      description:
        "Evidence is cross-checked and the final recommendation is explained — with sources cited, confidence shown, and any contradictions resolved visibly.",
      align: "left",
      visual: (
        <div className="w-full h-full flex flex-col justify-between p-6 bg-bg-sunken/90 rounded-xl border border-border">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="text-success size-4" />
              <span className="text-xs font-semibold uppercase tracking-wider text-text-primary">Validated Advisory</span>
            </div>
            <span className="text-[10px] bg-success/15 text-success px-2.5 py-0.5 rounded-full font-bold">98% Confidence</span>
          </div>
          <div className="my-3 p-3 bg-success/10 border border-success/30 rounded-lg">
            <span className="text-xs font-bold uppercase tracking-wider text-success block mb-1">Recommendation</span>
            <p className="text-sm font-semibold text-text-primary">
              SAFE TO OPERATE — Waves 1.2m, Wind 14 knots SW. No squall activity predicted.
            </p>
          </div>
          <div className="flex items-center justify-between text-[11px] text-text-secondary">
            <span>Sources: INCOIS Wave Buoy #4 + IMD Doppler</span>
            <Link href="/dashboard" className="text-primary font-semibold hover:underline flex items-center gap-1">
              View Map <ArrowRight className="size-3" />
            </Link>
          </div>
        </div>
      ),
    },
  ];

  return (
    <section className="py-24 md:py-32 px-6 lg:px-12 bg-background border-t border-border">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-24">
          <span className="text-primary text-sm font-semibold tracking-wide uppercase">Simple Workflow</span>
          <h2 className="font-heading font-bold text-4xl md:text-5xl text-foreground mt-3">
            Ask. Orchestrate. Validate.
          </h2>
        </div>

        <div className="flex flex-col gap-24">
          {steps.map((step) => (
            <div
              key={step.num}
              className={`flex flex-col ${
                step.align === "left" ? "md:flex-row" : "md:flex-row-reverse"
              } items-center gap-12 lg:gap-24`}
            >
              {/* Text Side */}
              <motion.div
                initial={{ opacity: 0, x: step.align === "left" ? -40 : 40 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6 }}
                className="w-full md:w-1/2"
              >
                <div className="text-primary font-heading font-bold text-6xl mb-6 opacity-50">
                  {step.num}
                </div>
                <h3 className="font-heading font-bold text-3xl text-foreground mb-4">
                  {step.title}
                </h3>
                <p className="text-xl text-muted-foreground leading-relaxed mb-6">
                  {step.description}
                </p>
              </motion.div>

              {/* Visual Mockup Card */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="w-full md:w-1/2"
              >
                <div className="w-full aspect-[4/3] rounded-2xl bg-card border border-border p-3 shadow-[0_0_40px_rgba(0,255,255,0.04)]">
                  {step.visual}
                </div>
              </motion.div>
            </div>
          ))}
        </div>

        <div className="mt-20 text-center">
          <Button asChild size="lg" className="bg-primary text-primary-foreground font-bold hover:scale-105 transition-transform">
            <Link href="/dashboard">Test the Workflow Live</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
