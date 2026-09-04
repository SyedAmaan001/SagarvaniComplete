import { Nav } from "@/components/layout/Nav";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/home/Hero";
import { WhatSetsApart } from "@/components/home/WhatSetsApart";
import { CTABanner } from "@/components/home/CTABanner";
import { HowItWorks } from "@/components/home/HowItWorks";
import { TheAgents } from "@/components/home/TheAgents";
import { SplitCardSection } from "@/components/home/SplitCardSection";
import { WavesSection } from "@/components/home/WavesSection";
import { ThreeSteps } from "@/components/home/ThreeSteps";
import { Reliability } from "@/components/home/Reliability";
import { CaseStudyFlipStack } from "@/components/visual/CaseStudyFlipStack";
import { Impact } from "@/components/home/Impact";
import { FAQ } from "@/components/home/FAQ";
import { AccessEverywhere } from "@/components/home/AccessEverywhere";
import { FinalCTA } from "@/components/home/FinalCTA";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col bg-background selection:bg-primary/30">
      {/* Phase 2: Navigation */}
      <Nav />

      {/* Phase 3: Hero (WebGLLiquid + WaveHero dynamics + Live Agent Matrix + Marquee) */}
      <Hero />

      {/* Phase 4: Why Sagarvani (3 core differentiators) */}
      <WhatSetsApart />

      {/* CTA Interstitial */}
      <CTABanner />

      {/* Phase 5: How It Works (Understand, Orchestrate, Validate tabs) */}
      <HowItWorks />

      {/* Phase 6 & 7: The Agents (3D DepthCarousel + BorderGlow + 6 Specialists Grid) */}
      <TheAgents />

      {/* Phase 8: NEW Stakeholder Explorer (8 real marine stakeholder groups) */}
      <SplitCardSection />

      {/* Phase 9: Real-time Ocean Intelligence (GradientWaves + 4 metrics) */}
      <WavesSection />

      {/* Phase 10: Three-Step Workflow (Natural Query -> Agent Dispatch -> Validated Advisory) */}
      <ThreeSteps />

      {/* Phase 11: Reliability & Validation (Fanned cards) */}
      <Reliability />

      {/* Phase 12: CaseStudyFlipStack (Scroll-driven stakeholder product scenarios) */}
      <CaseStudyFlipStack />

      {/* Phase 13: Impact Carousel */}
      <Impact />

      {/* Phase 14: FAQ */}
      <FAQ />

      {/* Phase 15: Access Everywhere */}
      <AccessEverywhere />

      {/* Phase 16: Final CTA */}
      <FinalCTA />

      {/* Phase 17: Footer */}
      <Footer />
    </main>
  );
}
