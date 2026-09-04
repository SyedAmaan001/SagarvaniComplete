import { Nav } from "@/components/layout/Nav";
import { Footer } from "@/components/layout/Footer";
import { FinalCTA } from "@/components/home/FinalCTA";
import { Database, Satellite, CloudRain, Radio, Waves, ShieldCheck } from "lucide-react";

export const metadata = {
  title: "Data Sources & Provenance — Sagarvani Ecosystem",
  description: "Explore the authoritative marine, meteorological, and earth observation feeds powering Sagarvani and the ORCA architecture.",
};

const sources = [
  {
    name: "INCOIS (Indian National Centre for Ocean Information Services)",
    agency: "Ministry of Earth Sciences (MoES), Govt. of India",
    icon: Waves,
    coverage: "Indian Ocean & EEZ",
    description: "Provides operational Potential Fishing Zone (PFZ) advisories, Ocean State Forecasts (OSF), sea surface temperature (SST), chlorophyll-a, significant wave height/period, surface current vectors, and tsunami/high-wave early warnings.",
    parameters: ["Significant Wave Height", "Peak Wave Period", "SST Gradients", "PFZ Polygons", "Tsunami Bulletins"]
  },
  {
    name: "IMD (India Meteorological Department)",
    agency: "Ministry of Earth Sciences (MoES), Govt. of India",
    icon: CloudRain,
    coverage: "National & Coastal Regions",
    description: "Supplies coastal weather bulletins, Doppler weather radar reflectivity, squall alerts, cyclone track forecasts, barometric pressure maps, and fishermen warning advisories.",
    parameters: ["Surface Wind Velocity", "Doppler Radar Reflectivity", "Cyclone Track Cones", "Heavy Rainfall Warnings"]
  },
  {
    name: "ISRO Bhuvan / NRSC",
    agency: "Indian Space Research Organisation (ISRO)",
    icon: Satellite,
    coverage: "Indian Landmass & Coastal Boundaries",
    description: "High-resolution satellite imagery, coastal geomorphology, bathymetry contours, coastal regulation zone (CRZ) boundaries, and disaster management support layers.",
    parameters: ["High-Res Optical Imagery", "Coastal Elevation", "CRZ Boundary GIS", "Nearshore Bathymetry"]
  },
  {
    name: "Bhoonidhi & MOSDAC",
    agency: "Space Applications Centre (SAC) & NRSC / ISRO",
    icon: Database,
    coverage: "Regional & Global Earth Observation",
    description: "Data dissemination portals for Indian remote sensing satellites (OceanSat-2/3, INSAT-3D/3DR, SCATSAT-1), providing ocean color monitors, sea surface roughness, and scatterometer wind vectors.",
    parameters: ["OceanSat-3 Ocean Color", "INSAT Thermal Imagery", "Scatterometer Winds", "Altimetry Swell Spectrum"]
  },
  {
    name: "BHASHINI & Sarvam AI",
    agency: "National Language Translation Mission (NLTM), MeitY",
    icon: Radio,
    coverage: "22 Official Indian Languages",
    description: "Multilingual speech-to-text, text-to-speech, and vernacular translation models enabling conversational access in Kannada, Tamil, Hindi, Telugu, Malayalam, Bengali, and Gujarati.",
    parameters: ["Speech Recognition (ASR)", "Text-to-Speech (TTS)", "Vernacular Domain Translation", "Phonetic Alignment"]
  },
  {
    name: "Supporting Geospatial & Modeling Stack",
    agency: "Open-Source & Global Marine Science",
    icon: ShieldCheck,
    coverage: "Global Standards",
    description: "Copernicus Marine Service, meteoblue numerical models, Leaflet GIS rendering, GeoPandas spatial indexing, and LangChain multi-agent orchestration.",
    parameters: ["GeoJSON Spatial Indexes", "Global Reanalysis Models", "Multi-Agent State Graph", "Vector DB Embeddings"]
  }
];

export default function DataSourcesPage() {
  return (
    <main className="flex min-h-screen flex-col bg-background text-foreground">
      <Nav />
      <div className="pt-32 pb-24 px-6 lg:px-12 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="text-center mb-16 max-w-3xl mx-auto">
          <span className="text-primary text-xs font-heading font-bold uppercase tracking-widest bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
            Data Architecture & Provenance
          </span>
          <h1 className="font-heading font-bold text-4xl md:text-6xl text-foreground mt-4">
            Authoritative Marine Feeds
          </h1>
          <p className="mt-4 text-text-secondary text-base leading-relaxed">
            Sagarvani does not generate speculative predictions from unverified sources. Every recommendation is anchored in official Indian and global earth observation telemetry.
          </p>
        </div>

        {/* Sources Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
          {sources.map((src) => (
            <div 
              key={src.name} 
              className="p-8 rounded-2xl border border-border bg-bg-elevated/70 flex flex-col justify-between shadow-xl"
            >
              <div>
                <div className="flex items-start justify-between gap-4 mb-5">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
                    <src.icon size={26} />
                  </div>
                  <span className="text-[10px] font-mono font-semibold uppercase text-primary px-2.5 py-1 rounded bg-bg-sunken border border-border">
                    {src.coverage}
                  </span>
                </div>
                <h3 className="font-heading font-bold text-xl text-foreground mb-1">{src.name}</h3>
                <span className="text-xs text-text-secondary font-mono block mb-4">{src.agency}</span>
                <p className="text-text-secondary text-sm leading-relaxed mb-6">{src.description}</p>
              </div>

              <div className="pt-4 border-t border-border/60">
                <span className="text-[10px] font-mono text-primary uppercase font-bold block mb-2">Key Integrated Telemetry:</span>
                <div className="flex flex-wrap gap-1.5">
                  {src.parameters.map((p) => (
                    <span key={p} className="px-2.5 py-1 rounded-md bg-bg-sunken border border-border/80 text-xs font-mono text-text-secondary">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <FinalCTA />
      <Footer />
    </main>
  );
}
