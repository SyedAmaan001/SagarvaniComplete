"use client";

import { GradientWaves } from "@/components/visual/GradientWaves";
import { motion } from "framer-motion";

export function WavesSection() {
  return (
    <section
      className="relative border-b border-border"
      style={{ minHeight: "60vh" }}
    >
      {/* WebGL wave background */}
      <GradientWaves
        horizonColor="#050A30"
        waveColor="#0000FF"
        crestColor="#00FFFF"
        speed={0.35}
        amplitude={2.8}
        waveScale={0.55}
        waveRatio={0.85}
        swell={38}
        turbulence={22}
        tilt={1.1}
        zoom={1.0}
        height={5.0}
        fogDepth={18}
        detail="medium"
        brightness={1.1}
        opacity={0.92}
        mouseInteraction={true}
        parallaxStrength={0.4}
        grain={true}
        grainIntensity={0.04}
        className="absolute inset-0 h-full"
      />

      {/* Overlay for readability */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "linear-gradient(to bottom, rgba(2,5,28,0.8) 0%, rgba(2,5,28,0.3) 40%, rgba(2,5,28,0.8) 100%)",
        }}
      />

      {/* Content */}
      <div className="relative z-10 flex min-h-[60vh] flex-col items-center justify-center px-6 py-24 text-center lg:px-12">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl"
        >
          <span className="text-sm font-semibold uppercase tracking-widest text-primary">
            Real-Time Ocean Intelligence
          </span>
          <h2 className="mt-4 font-heading text-4xl font-bold leading-tight text-white md:text-6xl">
            Where data meets the sea.
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-white/60">
            Sagarvani continuously processes live feeds from INCOIS, IMD, ISRO Bhuvan, and MOSDAC — 
            so every recommendation reflects the ocean as it actually is, right now.
          </p>
        </motion.div>

        {/* Live stats strip */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-16 grid grid-cols-2 gap-6 sm:grid-cols-4"
        >
          {[
            { label: "Data Sources", value: "8+" },
            { label: "Parameters Tracked", value: "40+" },
            { label: "Update Frequency", value: "15 min" },
            { label: "Coverage", value: "Indian EEZ" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-white/10 bg-white/5 px-6 py-4 text-center backdrop-blur-sm"
            >
              <p className="font-heading text-2xl font-bold text-primary">
                {stat.value}
              </p>
              <p className="mt-1 text-xs font-medium uppercase tracking-wider text-white/50">
                {stat.label}
              </p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
