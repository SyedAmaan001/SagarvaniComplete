import { Nav } from "@/components/layout/Nav";
import { Footer } from "@/components/layout/Footer";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Terminal, Award, BookOpen, ShieldCheck, MapPin } from "lucide-react";

export const metadata = {
  title: "Contact & Hackathon Info — Sagarvani",
  description: "Learn about Team Helios Luna, Dayananda Sagar University, and the Smart India Hackathon 2026 project SIH26176.",
};

export default function ContactPage() {
  return (
    <main className="flex min-h-screen flex-col bg-background text-foreground">
      <Nav />
      <div className="pt-32 pb-24 px-6 lg:px-12 max-w-5xl mx-auto w-full flex-1">
        {/* Header */}
        <div className="text-center mb-16 max-w-2xl mx-auto">
          <span className="text-primary text-xs font-heading font-bold uppercase tracking-widest bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
            Project & Team Information
          </span>
          <h1 className="font-heading font-bold text-4xl md:text-5xl text-foreground mt-4">
            Team Helios Luna
          </h1>
          <p className="mt-4 text-text-secondary text-base leading-relaxed">
            Developed for Smart India Hackathon 2026 to tackle disaster management and marine decision intelligence through collaborative multi-agent reasoning.
          </p>
        </div>

        {/* Project Credentials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          <div className="p-8 rounded-2xl border border-border bg-bg-elevated/70 shadow-xl flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-6">
                <Award size={26} />
              </div>
              <h3 className="font-heading font-bold text-2xl text-foreground mb-2">Hackathon Alignment</h3>
              <div className="space-y-2 text-sm text-text-secondary font-mono mt-4">
                <div><span className="text-primary font-bold">Initiative:</span> Smart India Hackathon 2026</div>
                <div><span className="text-primary font-bold">Problem Statement:</span> SIH26176</div>
                <div><span className="text-primary font-bold">Theme:</span> Disaster Management</div>
                <div><span className="text-primary font-bold">Category:</span> Software</div>
              </div>
            </div>
          </div>

          <div className="p-8 rounded-2xl border border-border bg-bg-elevated/70 shadow-xl flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-6">
                <BookOpen size={26} />
              </div>
              <h3 className="font-heading font-bold text-2xl text-foreground mb-2">Institution & Development</h3>
              <div className="space-y-2 text-sm text-text-secondary font-mono mt-4">
                <div><span className="text-primary font-bold">Team:</span> Helios Luna</div>
                <div><span className="text-primary font-bold">Institution:</span> Dayananda Sagar University</div>
                <div><span className="text-primary font-bold">Location:</span> Bengaluru, Karnataka, India</div>
                <div><span className="text-primary font-bold">Status:</span> Prototype Console Ready</div>
              </div>
            </div>
          </div>
        </div>

        {/* Call to Action Box */}
        <div className="p-10 rounded-3xl border border-border bg-bg-sunken text-center shadow-2xl relative overflow-hidden">
          <h3 className="font-heading font-bold text-2xl md:text-3xl text-foreground mb-4">
            Experience Sagarvani Live
          </h3>
          <p className="text-text-secondary text-sm md:text-base max-w-xl mx-auto mb-8 leading-relaxed">
            Test natural language queries, simulated contradiction handling, live multi-layer maps, and regional speech transcription in the mission control console.
          </p>
          <Button asChild size="lg" className="bg-primary text-bg-sunken font-bold px-8 py-6 rounded-xl hover:bg-primary/90 shadow-[0_0_25px_rgba(0,255,255,0.25)]">
            <Link href="/dashboard" className="flex items-center gap-2">
              <Terminal className="size-4" />
              <span>Launch Mission Console</span>
            </Link>
          </Button>
        </div>
      </div>
      <Footer />
    </main>
  );
}
