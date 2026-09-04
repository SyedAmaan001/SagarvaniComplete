"use client";

import { AgentStatus } from "@/lib/types";
import { 
  CheckCircle2, 
  CircleDashed, 
  Loader2, 
  AlertTriangle, 
  RefreshCw, 
  ShieldAlert,
  Waves,
  CloudRain,
  Map,
  LineChart,
  Compass,
  Cpu
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AgentStatusRailProps {
  agents: AgentStatus[];
}

const AGENT_ICONS: { [name: string]: React.ElementType } = {
  "Marine Data Agent": Waves,
  "Weather Agent": CloudRain,
  "GIS Agent": Map,
  "Ocean Analytics Agent": LineChart,
  "Risk Agent": ShieldAlert,
  "Spatial Reasoning Agent": Compass,
};

export function AgentStatusRail({ agents }: AgentStatusRailProps) {
  return (
    <div className="w-80 h-full bg-bg-primary border-l border-border flex flex-col p-4 shadow-2xl z-20 relative select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-3.5 mb-4 border-b border-border/70">
        <div className="flex items-center gap-2">
          <Cpu className="size-4 text-primary" />
          <h2 className="font-heading font-bold text-sm text-foreground uppercase tracking-wider">
            ORCA Specialists
          </h2>
        </div>
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full">
          6 Active
        </span>
      </div>

      {/* Agents List */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-0.5 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
        {agents.map((agent) => {
          const Icon = AGENT_ICONS[agent.name] || Waves;

          return (
            <div 
              key={agent.name} 
              className={`rounded-xl border p-3 transition-all duration-200 ${
                agent.state === "running" ? "border-primary bg-bg-elevated shadow-[0_0_15px_rgba(0,255,255,0.1)]" :
                agent.state === "conflict" ? "border-warning bg-warning/10 shadow-[0_0_15px_rgba(255,176,32,0.15)]" :
                agent.state === "rechecking" ? "border-warning bg-bg-elevated shadow-[0_0_15px_rgba(255,176,32,0.1)]" :
                agent.state === "validated" ? "border-border bg-bg-elevated/80" :
                "border-border/60 bg-bg-elevated/40"
              }`}
            >
              {/* Agent Title & State Icon */}
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-bg-sunken border border-border/80 flex items-center justify-center text-primary">
                    <Icon className="size-3.5" />
                  </div>
                  <div>
                    <h3 className="font-heading text-xs font-bold text-foreground">
                      {agent.name.replace(" Agent", "")}
                    </h3>
                    <span className="text-[9px] text-text-secondary block font-mono">
                      {agent.role}
                    </span>
                  </div>
                </div>

                <div className="flex items-center">
                  <AnimatePresence mode="wait">
                    {agent.state === "idle" && (
                      <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-1">
                        <CircleDashed className="w-3.5 h-3.5 text-text-secondary/50" />
                        <span className="text-[9px] font-mono text-text-secondary/60">IDLE</span>
                      </motion.div>
                    )}
                    {agent.state === "running" && (
                      <motion.div key="running" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-1">
                        <Loader2 className="w-3.5 h-3.5 text-primary animate-spin" />
                        <span className="text-[9px] font-mono text-primary font-bold">RUNNING</span>
                      </motion.div>
                    )}
                    {agent.state === "conflict" && (
                      <motion.div key="conflict" initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-1">
                        <AlertTriangle className="w-4 h-4 text-warning animate-pulse" />
                        <span className="text-[9px] font-mono text-warning font-bold">CONFLICT</span>
                      </motion.div>
                    )}
                    {agent.state === "rechecking" && (
                      <motion.div key="rechecking" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-1">
                        <RefreshCw className="w-4 h-4 text-warning animate-spin" />
                        <span className="text-[9px] font-mono text-warning font-bold">RE-CHECK</span>
                      </motion.div>
                    )}
                    {agent.state === "validated" && (
                      <motion.div key="validated" initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4 text-success" />
                        <span className="text-[9px] font-mono text-success font-bold">VALIDATED</span>
                      </motion.div>
                    )}
                    {agent.state === "degraded" && (
                      <motion.div key="degraded" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <span className="text-[9px] font-mono text-warning bg-warning/15 px-1.5 py-0.5 rounded">DEGRADED</span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              {/* Source Attribution & Details */}
              <div className="pt-2 border-t border-border/40 text-[10px] space-y-0.5 font-mono">
                <div className="flex items-center justify-between text-text-secondary">
                  <span>Feed:</span>
                  <span className="text-foreground truncate max-w-[170px]">{agent.source}</span>
                </div>
                {agent.latency && (
                  <div className="flex items-center justify-between text-text-secondary">
                    <span>Latency:</span>
                    <span className="text-primary">{agent.latency}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Consensus Integrity Footer */}
      <div className="mt-4 p-3 rounded-xl bg-bg-sunken border border-border flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-success" />
          <span className="text-text-secondary font-mono">Consensus Gate:</span>
        </div>
        <span className="font-mono text-success font-bold">ACTIVE</span>
      </div>
    </div>
  );
}
