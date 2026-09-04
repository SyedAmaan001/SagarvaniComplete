"use client";

import { motion, useReducedMotion } from "framer-motion";

interface WaveHeroProps {
  primaryColor?: string;
  secondaryColor?: string;
  baseColor?: string;
  speedMultiplier?: number;
}

export function WaveHero({
  primaryColor = "#00FFFF",
  secondaryColor = "#0000FF",
  baseColor = "#02051C",
  speedMultiplier = 1,
}: WaveHeroProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
      <div className="absolute inset-0 bg-bg-sunken" />

      {/* Ambient Radial Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-accent-cyan/15 via-accent-blue/10 to-transparent opacity-70 blur-2xl" />

      {/* SVG Multi-layer Wave Ocean Surface */}
      <div className="absolute bottom-0 left-0 right-0 w-full h-[60vh] min-h-[420px] flex items-end">
        <svg
          className="w-full h-full min-w-[1440px]"
          preserveAspectRatio="none"
          viewBox="0 0 1440 360"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="wave-grad-front" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={primaryColor} stopOpacity="0.85" />
              <stop offset="40%" stopColor={secondaryColor} stopOpacity="0.5" />
              <stop offset="100%" stopColor={baseColor} stopOpacity="0.95" />
            </linearGradient>

            <linearGradient id="wave-grad-mid" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={secondaryColor} stopOpacity="0.75" />
              <stop offset="60%" stopColor="#0B1550" stopOpacity="0.4" />
              <stop offset="100%" stopColor={baseColor} stopOpacity="0.9" />
            </linearGradient>

            <linearGradient id="wave-grad-back" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={primaryColor} stopOpacity="0.25" />
              <stop offset="100%" stopColor={baseColor} stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Deep Back Ocean Undulation */}
          <motion.path
            d="M0,220 C240,160, 480,280, 720,200 C960,120, 1200,240, 1440,180 C1680,120, 1920,240, 2160,180 L2160,360 L0,360 Z"
            fill="url(#wave-grad-back)"
            animate={
              shouldReduceMotion
                ? undefined
                : {
                    x: [0, -720],
                  }
            }
            transition={{
              repeat: Infinity,
              ease: "linear",
              duration: 24 / speedMultiplier,
            }}
          />

          {/* Mid Ocean Current Swell */}
          <motion.path
            d="M0,170 C300,250, 600,100, 900,190 C1200,280, 1500,120, 1800,210 C2100,300, 2400,140, 2700,210 L2700,360 L0,360 Z"
            fill="url(#wave-grad-mid)"
            animate={
              shouldReduceMotion
                ? undefined
                : {
                    x: [0, -900],
                  }
            }
            transition={{
              repeat: Infinity,
              ease: "linear",
              duration: 16 / speedMultiplier,
            }}
          />

          {/* Cresting Front Kinetic Wave */}
          <motion.path
            d="M0,200 C240,120, 480,260, 720,180 C960,100, 1200,220, 1440,160 C1680,100, 1920,220, 2160,160 L2160,360 L0,360 Z"
            fill="url(#wave-grad-front)"
            animate={
              shouldReduceMotion
                ? undefined
                : {
                    x: [0, -720],
                    d: [
                      "M0,200 C240,120, 480,260, 720,180 C960,100, 1200,220, 1440,160 C1680,100, 1920,220, 2160,160 L2160,360 L0,360 Z",
                      "M0,180 C240,240, 480,140, 720,210 C960,280, 1200,150, 1440,200 C1680,250, 1920,150, 2160,200 L2160,360 L0,360 Z",
                      "M0,200 C240,120, 480,260, 720,180 C960,100, 1200,220, 1440,160 C1680,100, 1920,220, 2160,160 L2160,360 L0,360 Z",
                    ],
                  }
            }
            transition={{
              x: {
                repeat: Infinity,
                ease: "linear",
                duration: 10 / speedMultiplier,
              },
              d: {
                repeat: Infinity,
                repeatType: "reverse",
                ease: "easeInOut",
                duration: 6 / speedMultiplier,
              },
            }}
          />
        </svg>
      </div>

      {/* Depth atmospheric fade */}
      <div className="absolute inset-0 bg-gradient-to-b from-bg-primary via-transparent to-bg-primary/90 pointer-events-none" />
    </div>
  );
}
