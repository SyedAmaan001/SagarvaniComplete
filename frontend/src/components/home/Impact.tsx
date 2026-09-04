"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function Impact() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  const impacts = [
    {
      persona: "Social Impact",
      stat: "More accessible marine information",
      description: "Local-language and voice pathways make marine intelligence available to communities that lack smartphones or stable internet connections. Low-connectivity design ensures no one is excluded."
    },
    {
      persona: "Economic Impact",
      stat: "Better-informed operational decisions",
      description: "Reduces manual effort in interpreting fragmented information from multiple agencies. Supports marine operations and research workflows with fused, validated intelligence."
    },
    {
      persona: "Environmental Impact",
      stat: "Spatial understanding of marine conditions",
      description: "Better access to ocean-state and environmental indicators through integrated satellite, buoy, and model data. Evidence-oriented decision support for marine stewardship."
    },
    {
      persona: "Fishermen & Coastal Crews",
      stat: "Simple, understandable marine guidance",
      description: "Combines weather, wave, ocean, and risk context into one explainable interaction — location-aware and accessible through voice or low-bandwidth channels."
    },
    {
      persona: "Marine & Port Operators",
      stat: "Operational situational awareness",
      description: "Spatial intelligence, alerts, environmental conditions, and evidence — brought together into a single conversational interface for route and context decisions."
    },
    {
      persona: "Disaster Management & Coastal Safety",
      stat: "Rapid situational awareness",
      description: "Consolidated environmental signals, spatial context, and visible validation — designed for rapid response when coastal safety is at stake."
    }
  ];

  useEffect(() => {
    if (isHovered) return;
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % impacts.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [isHovered, impacts.length]);

  const prev = () => setCurrentIndex((prev) => (prev - 1 + impacts.length) % impacts.length);
  const next = () => setCurrentIndex((prev) => (prev + 1) % impacts.length);

  return (
    <section id="impact" className="py-24 md:py-32 px-6 lg:px-12 bg-background">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-end mb-16 gap-6">
          <div>
            <span className="text-sm font-semibold tracking-wider text-muted-foreground uppercase mb-4 block">Impact</span>
            <h2 className="font-heading font-bold text-4xl md:text-5xl text-foreground">Who it helps</h2>
          </div>
          <div className="flex gap-4">
            <button onClick={prev} className="w-12 h-12 rounded-full border border-border flex items-center justify-center hover:bg-card hover:border-primary/50 transition-colors">
              <ChevronLeft className="text-foreground" />
            </button>
            <button onClick={next} className="w-12 h-12 rounded-full border border-border flex items-center justify-center hover:bg-card hover:border-primary/50 transition-colors">
              <ChevronRight className="text-foreground" />
            </button>
          </div>
        </div>

        <div 
          className="relative w-full h-[320px] overflow-hidden rounded-2xl"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <AnimatePresence mode="popLayout">
            <motion.div
              key={currentIndex}
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
              className="absolute inset-0 bg-card border border-border rounded-2xl p-10 md:p-16 flex flex-col justify-center"
            >
              <span className="inline-block px-4 py-1.5 rounded-full bg-background border border-border text-primary font-semibold text-sm w-fit mb-6">
                {impacts[currentIndex].persona}
              </span>
              <h3 className="font-heading font-bold text-3xl md:text-4xl text-foreground mb-6">
                {impacts[currentIndex].stat}
              </h3>
              <p className="text-xl text-muted-foreground max-w-3xl leading-relaxed">
                {impacts[currentIndex].description}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
