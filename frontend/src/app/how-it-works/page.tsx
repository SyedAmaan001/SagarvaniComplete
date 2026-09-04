import { Nav } from "@/components/layout/Nav";
import { Footer } from "@/components/layout/Footer";
import { HowItWorks } from "@/components/home/HowItWorks";
import { TheAgents } from "@/components/home/TheAgents";
import { ThreeSteps } from "@/components/home/ThreeSteps";
import { Reliability } from "@/components/home/Reliability";
import { FinalCTA } from "@/components/home/FinalCTA";

export const metadata = {
  title: "How It Works — ORCA Multi-Agent Architecture",
  description: "Explore the ORCA marine multi-agent architecture, from natural language query to parallel specialist execution, contradiction checks, and validated advisories.",
};

export default function HowItWorksPage() {
  return (
    <main className="flex min-h-screen flex-col bg-background text-foreground">
      <Nav />
      <div className="pt-24">
        <HowItWorks />
        <TheAgents />
        <ThreeSteps />
        <Reliability />
        <FinalCTA />
      </div>
      <Footer />
    </main>
  );
}
