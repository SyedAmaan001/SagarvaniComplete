import Link from "next/link";
import Image from "next/image";

export function Footer() {
  return (
    <footer className="bg-bg-sunken border-t border-border pt-16 pb-12 px-6 lg:px-12 text-text-secondary">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          {/* Col 1: Brand & Problem Statement */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-3.5 mb-5">
              <div className="relative w-11 h-11 rounded-xl overflow-hidden border border-[#1B2A6B]/80 bg-[#0B1550]/40 p-1 flex items-center justify-center shadow-[0_0_15px_rgba(0,255,255,0.15)]">
                <Image
                  src="/logo.png"
                  alt="Sagarvani Logo"
                  width={44}
                  height={44}
                  className="object-contain w-full h-full scale-105"
                />
              </div>
              <span className="font-heading font-bold text-xl uppercase tracking-wider text-foreground">
                Sagarvani
              </span>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed max-w-md mb-4">
              Conversational Marine Decision-Intelligence Platform. 
              Powered by the ORCA multi-agent reasoning architecture to fuse ocean, weather, GIS, and risk data into validated, explainable recommendations.
            </p>
            <div className="inline-flex flex-wrap gap-2 text-xs font-mono">
              <span className="px-2.5 py-1 rounded bg-bg-elevated border border-border text-primary">
                SIH26176
              </span>
              <span className="px-2.5 py-1 rounded bg-bg-elevated border border-border text-text-secondary">
                Theme: Disaster Management
              </span>
              <span className="px-2.5 py-1 rounded bg-bg-elevated border border-border text-text-secondary">
                Category: Software
              </span>
            </div>
          </div>
          
          {/* Col 2: Navigation */}
          <div>
            <h4 className="font-heading font-semibold text-sm uppercase tracking-wider text-foreground mb-4">
              Platform
            </h4>
            <ul className="space-y-3 text-sm">
              <li><Link href="/solutions" className="hover:text-primary transition-colors">Stakeholder Solutions</Link></li>
              <li><Link href="/how-it-works" className="hover:text-primary transition-colors">How ORCA Works</Link></li>
              <li><Link href="/access" className="hover:text-primary transition-colors">Access Channels</Link></li>
              <li><Link href="/data-sources" className="hover:text-primary transition-colors">Data Provenance</Link></li>
              <li><Link href="/dashboard" className="text-primary hover:underline font-semibold flex items-center gap-1">Launch Console →</Link></li>
            </ul>
          </div>
          
          {/* Col 3: Research & Ingestion Partners */}
          <div>
            <h4 className="font-heading font-semibold text-sm uppercase tracking-wider text-foreground mb-4">
              Data Ecosystem
            </h4>
            <ul className="space-y-3 text-sm">
              <li><span className="hover:text-foreground transition-colors">INCOIS (MoES, Govt. of India)</span></li>
              <li><span className="hover:text-foreground transition-colors">IMD (MoES, Govt. of India)</span></li>
              <li><span className="hover:text-foreground transition-colors">ISRO Bhuvan / NRSC</span></li>
              <li><span className="hover:text-foreground transition-colors">Bhoonidhi & MOSDAC</span></li>
              <li><span className="hover:text-foreground transition-colors">BHASHINI & Sarvam AI</span></li>
            </ul>
          </div>
        </div>
        
        {/* Compliance Footer Bar */}
        <div className="border-t border-border pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-xs">
          <p className="text-text-secondary">
            Built for Smart India Hackathon 2026 · Problem Statement SIH26176 · Team Helios Luna, Dayananda Sagar University.
          </p>
          <p className="text-[11px] text-text-secondary/70">
            Decision support system. Always consult official maritime warnings during active cyclone alerts.
          </p>
        </div>
      </div>
    </footer>
  );
}
