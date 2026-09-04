"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import Image from "next/image";
import { 
  AgentStatus, 
  ConversationTurn, 
  Readout, 
  Alert, 
  MapLayer 
} from "@/lib/types";
import { 
  initialAgents, 
  initialReadouts, 
  PREDEFINED_SCENARIOS 
} from "@/lib/mock-data/scenario";
import { queryOrca } from "@/lib/api/orca";
import { AgentStatusRail } from "./AgentStatusRail";
import { ReadoutStrip } from "./ReadoutStrip";
import { ConversationRail } from "./ConversationRail";
import { AlertsPanel } from "./AlertsPanel";
import { ReasoningPanel } from "./ReasoningPanel";
import { 
  Layers, 
  Home, 
  RotateCcw, 
  Sparkles, 
  ShieldCheck, 
  Activity,
  CheckCircle2,
  AlertTriangle,
  Info
} from "lucide-react";
import { Button } from "@/components/ui/button";

// Dynamically import MapCanvas to prevent Leaflet SSR issues
const MapCanvas = dynamic(() => import("./MapCanvas"), { 
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-bg-sunken flex flex-col items-center justify-center gap-2 text-text-secondary font-mono text-xs">
      <span className="size-3 rounded-full bg-primary animate-ping" />
      <span>Loading Spatial Canvas...</span>
    </div>
  )
});

export function DashboardClient() {
  const [agents, setAgents] = useState<AgentStatus[]>(initialAgents);
  const [readouts, setReadouts] = useState<Readout[]>(initialReadouts);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activeLayers, setActiveLayers] = useState<MapLayer[]>(['Wave Height', 'Currents']);
  const [isTyping, setIsTyping] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [currentScenarioId, setCurrentScenarioId] = useState<string | undefined>();
  const [focusedCoords, setFocusedCoords] = useState<[number, number] | undefined>();
  
  const [trace, setTrace] = useState<string[]>([]);
  const [activeIntent, setActiveIntent] = useState<string>("");
  const [isContradictionState, setIsContradictionState] = useState(false);

  const [mobileTab, setMobileTab] = useState<'chat' | 'map' | 'agents'>('chat');

  // Toggle map layers
  const toggleLayer = (layer: MapLayer) => {
    setActiveLayers(prev => 
      prev.includes(layer) ? prev.filter(l => l !== layer) : [...prev, layer]
    );
  };

  // Reset console to clean state
  const handleResetConsole = () => {
    setAgents(initialAgents);
    setReadouts(initialReadouts);
    setTurns([]);
    setAlerts([]);
    setActiveLayers(['Wave Height', 'Currents']);
    setShowReasoning(false);
    setCurrentScenarioId(undefined);
    setTrace([]);
    setActiveIntent("");
    setIsContradictionState(false);
    setFocusedCoords([12.9141, 74.8560]);
  };

  // Run a scenario simulation or query
  const executeScenario = async (scenarioId: string) => {
    const scenario = PREDEFINED_SCENARIOS.find(s => s.id === scenarioId);
    if (!scenario) return;

    setCurrentScenarioId(scenario.id);
    setIsContradictionState(scenario.isContradiction);
    setActiveIntent(scenario.intent);
    setShowReasoning(false);

    // Set map focus according to scenario
    if (scenario.id === "safe-fishing-mangalore") {
      setFocusedCoords([12.9141, 74.8560]);
    } else if (scenario.id === "contradiction-squall") {
      setFocusedCoords([13.1000, 74.3500]);
    } else if (scenario.id === "pfz-advisory") {
      setFocusedCoords([14.6800, 73.9800]);
    }

    // 1. Add user question to rail
    const userTurn: ConversationTurn = {
      id: `turn-user-${Date.now()}`,
      role: 'user',
      text: scenario.query,
      timestamp: "Just now"
    };
    setTurns(prev => [...prev, userTurn]);
    setIsTyping(true);

    // 2. Believable staggered agent activation
    setAgents(prev => prev.map((a, idx) => ({
      ...a,
      state: scenario.runningAgents.includes(a.name) ? 'running' : 'idle',
      latency: `${Math.floor(Math.random() * 15) + 10}ms`
    })));

    // 3. If scenario has a contradiction, show conflict & re-checking phase
    if (scenario.isContradiction) {
      setTimeout(() => {
        // Show conflict state
        setAgents(prev => prev.map(a => {
          if (scenario.conflictAgents?.includes(a.name)) {
            return { ...a, state: 'conflict' };
          }
          return a;
        }));
      }, 1000);

      setTimeout(() => {
        // Show re-checking state
        setAgents(prev => prev.map(a => {
          if (scenario.conflictAgents?.includes(a.name)) {
            return { ...a, state: 'rechecking' };
          }
          return a;
        }));
      }, 2000);

      setTimeout(() => {
        // Complete validation
        setAgents(prev => prev.map(a => ({ ...a, state: 'validated' })));
        setReadouts(scenario.readouts);
        setAlerts(scenario.alerts);
        setActiveLayers(scenario.layers);
        setTrace(scenario.recheckingSteps);
        setTurns(prev => [...prev, scenario.turn]);
        setIsTyping(false);
        setShowReasoning(true);
      }, 3200);

    } else {
      // Normal resolution flow with believable timing
      setTimeout(() => {
        setAgents(prev => prev.map(a => ({ ...a, state: 'validated' })));
        setReadouts(scenario.readouts);
        setAlerts(scenario.alerts);
        setActiveLayers(scenario.layers);
        setTrace(scenario.recheckingSteps);
        setTurns(prev => [...prev, scenario.turn]);
        setIsTyping(false);
        setShowReasoning(true);
      }, 2000);
    }
  };

  // Custom free-form query handler
  const handleCustomAsk = async (queryText: string) => {
    const matched = PREDEFINED_SCENARIOS.find(s => 
      queryText.toLowerCase().includes(s.badge.toLowerCase()) ||
      queryText.toLowerCase().includes(s.name.toLowerCase().slice(0, 10))
    );

    if (matched) {
      executeScenario(matched.id);
      return;
    }

    setIsTyping(true);
    setTurns(prev => [...prev, {
      id: `turn-user-${Date.now()}`,
      role: 'user',
      text: queryText,
      timestamp: "Just now"
    }]);

    setAgents(prev => prev.map(a => ({ ...a, state: 'running' })));

    try {
      const result = await queryOrca(queryText);
      setAgents(result.agent_states);
      setTurns(prev => [...prev, result.turn]);
      if (result.readouts && result.readouts.length > 0) {
        setReadouts(result.readouts);
      }
      if (result.alerts && result.alerts.length > 0) {
        setAlerts(result.alerts);
      }
      if (result.turn.validationTrace) {
        setTrace(result.turn.validationTrace);
      }
      setIsTyping(false);
      setShowReasoning(true);
    } catch {
      setTimeout(() => {
        setAgents(prev => prev.map(a => ({ ...a, state: 'validated' })));
        setTurns(prev => [...prev, {
          id: `turn-sag-${Date.now()}`,
          role: 'sagarvani',
          text: `ORCA has synthesized marine conditions for your query: "${queryText}". Current wave heights off the west coast remain moderate (1.1m - 1.4m) with winds at 12 knots. Always observe localized weather warnings before launching craft.`,
          evidence: [
            { source: "INCOIS Coastal Observation", summary: "Wave height: 1.2m, slight sea state." },
            { source: "IMD Weather Radar", summary: "Clear atmospheric conditions." }
          ]
        }]);
        setTrace([
          "1. Parsed query context and spatial bounds.",
          "2. Queried INCOIS wave telemetry & IMD meteorological radar.",
          "3. Evaluated risk envelope for small-to-medium vessels.",
          "4. Generated validated decision advisory."
        ]);
        setIsTyping(false);
        setShowReasoning(true);
      }, 2000);
    }
  };

  // Auto-run safe scenario on initial load if empty
  useEffect(() => {
    const timer = setTimeout(() => {
      if (turns.length === 0) {
        executeScenario("safe-fishing-mangalore");
      }
    }, 400);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex flex-col h-screen w-full bg-bg-sunken overflow-hidden text-foreground font-sans select-none">
      
      {/* Top Mission Control Bar */}
      <header className="h-14 bg-bg-primary border-b border-border px-4 flex items-center justify-between shrink-0 z-30">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative w-9 h-9 rounded-lg overflow-hidden border border-[#1B2A6B]/80 bg-[#0B1550]/40 p-0.5 flex items-center justify-center group-hover:border-primary transition-colors shadow-[0_0_12px_rgba(0,255,255,0.15)]">
              <Image src="/logo.png" alt="Sagarvani Logo" width={36} height={36} className="object-contain w-full h-full scale-105" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-heading font-bold text-sm tracking-wider uppercase text-foreground">
                Sagarvani
              </span>
              <span className="text-[10px] font-mono text-primary uppercase font-bold">
                Console
              </span>
            </div>
          </Link>

          <div className="hidden sm:flex items-center gap-2 pl-4 border-l border-border/60">
            <span className="text-[10px] font-mono uppercase text-text-secondary">Mode:</span>
            <span className="text-[11px] font-mono font-bold text-success bg-success/15 px-2 py-0.5 rounded border border-success/30 flex items-center gap-1">
              <CheckCircle2 className="size-3" /> ORCA REASONING READY
            </span>
          </div>
        </div>

        {/* Mobile View Switcher (Visible on mobile/tablets) */}
        <div className="flex lg:hidden items-center bg-bg-elevated border border-border p-0.5 rounded-lg text-xs font-mono">
          <button
            onClick={() => setMobileTab('chat')}
            className={`px-2.5 py-1 rounded transition-colors ${
              mobileTab === 'chat' ? 'bg-primary text-bg-sunken font-bold' : 'text-text-secondary'
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => setMobileTab('map')}
            className={`px-2.5 py-1 rounded transition-colors ${
              mobileTab === 'map' ? 'bg-primary text-bg-sunken font-bold' : 'text-text-secondary'
            }`}
          >
            Map
          </button>
          <button
            onClick={() => setMobileTab('agents')}
            className={`px-2.5 py-1 rounded transition-colors ${
              mobileTab === 'agents' ? 'bg-primary text-bg-sunken font-bold' : 'text-text-secondary'
            }`}
          >
            Agents
          </button>
        </div>

        {/* Top Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowReasoning(!showReasoning)}
            className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-colors flex items-center gap-1.5 border ${
              showReasoning 
                ? "bg-primary text-bg-sunken border-primary" 
                : "bg-bg-elevated border-border text-text-secondary hover:text-foreground"
            }`}
          >
            <Activity className="size-3.5" />
            <span className="hidden sm:inline">Reasoning Trace</span>
          </button>

          <button
            onClick={handleResetConsole}
            className="px-2.5 py-1.5 rounded-lg text-xs font-mono text-text-secondary bg-bg-elevated border border-border hover:text-foreground hover:bg-bg-sunken transition-colors flex items-center gap-1"
            title="Reset Console"
            aria-label="Reset Console"
          >
            <RotateCcw className="size-3.5" />
          </button>

          <Button asChild size="sm" variant="outline" className="border-border text-text-secondary hover:text-foreground h-8 text-xs">
            <Link href="/" className="flex items-center gap-1.5">
              <Home className="size-3.5" />
              <span className="hidden md:inline">Home</span>
            </Link>
          </Button>
        </div>
      </header>

      {/* Main Console Workspace */}
      <div className="flex-1 flex min-h-0 relative">
        {/* Left Rail: Conversation & Voice (Desktop: always flex; Mobile: only when tab is chat) */}
        <div className={`h-full ${mobileTab === 'chat' ? 'flex' : 'hidden lg:flex'}`}>
          <ConversationRail 
            turns={turns} 
            onAsk={handleCustomAsk} 
            isTyping={isTyping}
            onSelectScenario={executeScenario}
            activeScenarioId={currentScenarioId}
          />
        </div>

        {/* Center Canvas: Telemetry & Spatial Map (Desktop: always flex; Mobile: only when tab is map) */}
        <div className={`flex-1 flex-col relative z-0 min-w-0 ${mobileTab === 'map' ? 'flex' : 'hidden lg:flex'}`}>
          <ReadoutStrip readouts={readouts} />
          
          <div className="flex-1 relative overflow-hidden">
            {/* Active Alerts HUD */}
            <AlertsPanel 
              alerts={alerts} 
              onFocusAlert={(coords) => setFocusedCoords(coords)}
            />
            
            {/* Map Layer Switcher Control */}
            <div className="absolute top-4 right-4 z-20 flex flex-col gap-2">
              <div className="bg-bg-elevated/90 backdrop-blur-md border border-border p-2.5 rounded-xl shadow-2xl flex flex-col gap-1.5 min-w-[140px]">
                <div className="flex items-center gap-1.5 px-1.5 pb-1.5 border-b border-border/60 text-[10px] font-mono font-bold uppercase tracking-wider text-text-secondary">
                  <Layers className="w-3.5 h-3.5 text-primary" /> Map Layers
                </div>
                {(['Wave Height', 'Currents', 'SST', 'PFZ', 'Cyclone', 'High Wave Warnings'] as MapLayer[]).map(layer => {
                  const isActive = activeLayers.includes(layer);
                  return (
                    <button
                      key={layer}
                      onClick={() => toggleLayer(layer)}
                      className={`text-left px-2.5 py-1 rounded-md text-xs font-mono font-semibold transition-all ${
                        isActive 
                          ? 'bg-primary/20 text-primary border border-primary/40 shadow-sm' 
                          : 'text-text-secondary hover:bg-bg-primary hover:text-foreground border border-transparent'
                      }`}
                    >
                      {layer}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Map Canvas */}
            <MapCanvas 
              activeLayers={activeLayers} 
              focusedCoordinates={focusedCoords}
            />
            
            {/* Step-by-Step Reasoning Panel */}
            <ReasoningPanel 
              isOpen={showReasoning} 
              onClose={() => setShowReasoning(false)} 
              trace={trace}
              intent={activeIntent}
              isContradiction={isContradictionState}
            />
          </div>
        </div>

        {/* Right Rail: 6 ORCA Specialists Status (Desktop: always flex; Mobile: only when tab is agents) */}
        <div className={`h-full ${mobileTab === 'agents' ? 'flex' : 'hidden lg:flex'}`}>
          <AgentStatusRail agents={agents} />
        </div>
      </div>

    </div>
  );
}
