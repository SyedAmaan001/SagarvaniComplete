import { Nav } from "@/components/layout/Nav";
import { Footer } from "@/components/layout/Footer";
import { AccessEverywhere } from "@/components/home/AccessEverywhere";
import { CaseStudyFlipStack } from "@/components/visual/CaseStudyFlipStack";
import { FinalCTA } from "@/components/home/FinalCTA";

export const metadata = {
  title: "Access Channels — Web, App, Helpline & Low-Bandwidth",
  description: "Learn how Sagarvani delivers critical ocean intelligence across smartphones, voice helplines, and low-bandwidth coastal portals.",
};

export default function AccessPage() {
  return (
    <main className="flex min-h-screen flex-col bg-background text-foreground">
      <Nav />
      <div className="pt-24">
        <AccessEverywhere />
        <CaseStudyFlipStack />
        <FinalCTA />
      </div>
      <Footer />
    </main>
  );
}
