import { Nav } from "@/components/layout/Nav";
import { Footer } from "@/components/layout/Footer";
import { SplitCardSection } from "@/components/home/SplitCardSection";
import { WhatSetsApart } from "@/components/home/WhatSetsApart";
import { FinalCTA } from "@/components/home/FinalCTA";

export const metadata = {
  title: "Solutions — Sagarvani Ocean Decision Intelligence",
  description: "Tailored marine decision intelligence for fishermen, port operators, scientists, emergency managers, and offshore industry.",
};

export default function SolutionsPage() {
  return (
    <main className="flex min-h-screen flex-col bg-background text-foreground">
      <Nav />
      <div className="pt-24">
        <WhatSetsApart />
        <SplitCardSection />
        <FinalCTA />
      </div>
      <Footer />
    </main>
  );
}
