"use client";

import { Button } from "@/components/ui/button";
import Link from "next/link";
import { motion } from "framer-motion";
import { Terminal, ArrowRight } from "lucide-react";

export function FinalCTA() {
  return (
    <section className="relative py-32 px-6 lg:px-12 bg-bg-sunken border-t border-border overflow-hidden flex flex-col items-center justify-center text-center">
      {/* Decorative background wave line glow */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-40">
        <svg viewBox="0 0 1000 400" className="w-full h-full max-w-5xl" preserveAspectRatio="none">
          <path 
            d="M 0 400 C 300 100, 700 100, 1000 400" 
            fill="none" 
            stroke="url(#cta-glow)" 
            strokeWidth="3" 
          />
          <defs>
            <linearGradient id="cta-glow" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#050A30" stopOpacity="0" />
              <stop offset="50%" stopColor="#00FFFF" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#050A30" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/10 via-transparent to-transparent"></div>

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="relative z-10 max-w-3xl mx-auto"
      >
        <span className="text-primary text-xs font-heading font-bold uppercase tracking-widest bg-primary/10 border border-primary/20 px-4 py-1.5 rounded-full inline-block mb-6">
          Step Into Sagarvani
        </span>
        <h2 className="font-heading font-bold text-4xl md:text-6xl text-foreground mb-6 tracking-tight leading-tight">
          Marine Intelligence for Everyone
        </h2>
        <p className="text-text-secondary text-base md:text-lg mb-10 max-w-2xl mx-auto leading-relaxed">
          From open water to the coastline — one validated answer, however you reach us.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button 
            asChild 
            size="lg" 
            className="bg-primary text-bg-sunken hover:bg-primary/90 font-bold px-10 py-7 text-base rounded-xl shadow-[0_0_35px_rgba(0,255,255,0.3)] hover:scale-[1.03] transition-transform duration-150"
          >
            <Link href="/dashboard" className="flex items-center gap-2.5">
              <Terminal className="size-5" />
              <span>Try Sagarvani</span>
            </Link>
          </Button>
          <Button 
            asChild 
            variant="outline"
            size="lg" 
            className="border-border text-foreground bg-bg-elevated/40 hover:bg-bg-elevated hover:text-primary px-8 py-7 text-base rounded-xl transition-colors"
          >
            <Link href="/how-it-works" className="flex items-center gap-2">
              <span>Explore Architecture</span>
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </motion.div>
    </section>
  );
}
