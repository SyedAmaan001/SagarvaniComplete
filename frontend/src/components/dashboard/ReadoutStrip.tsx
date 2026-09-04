"use client";

import { Readout } from "@/lib/types";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";

export function ReadoutStrip({ readouts }: { readouts: Readout[] }) {
  return (
    <div className="h-[68px] w-full bg-bg-primary/95 backdrop-blur-md border-b border-border flex items-center px-6 gap-8 overflow-x-auto shadow-sm select-none scrollbar-none">
      {readouts.map((readout, idx) => (
        <div key={idx} className="flex flex-col relative h-full justify-center shrink-0">
          <div className="flex items-baseline gap-1.5">
            <span className="font-heading font-bold text-xl text-foreground leading-none">
              {readout.value}
            </span>
            {readout.unit && (
              <span className="text-[10px] text-text-secondary font-mono font-semibold uppercase tracking-wider">
                {readout.unit}
              </span>
            )}
            {readout.trend === 'up' && <ArrowUp className="size-3 text-warning shrink-0" />}
            {readout.trend === 'down' && <ArrowDown className="size-3 text-success shrink-0" />}
            {readout.trend === 'stable' && <Minus className="size-3 text-text-secondary/50 shrink-0" />}
          </div>
          <span className="text-[9px] text-text-secondary uppercase font-bold tracking-widest mt-1 font-mono">
            {readout.label}
          </span>
          
          {readout.isActive && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary shadow-[0_0_8px_rgba(0,255,255,0.8)]" />
          )}
        </div>
      ))}

      {/* Live System Time Readout */}
      <div className="ml-auto flex items-center gap-3 shrink-0 pl-4 border-l border-border/60 text-xs font-mono">
        <div className="flex flex-col items-end">
          <span className="text-[10px] text-text-secondary uppercase tracking-widest font-semibold">
            Indian EEZ Grid
          </span>
          <span className="text-primary font-bold">12.91°N, 74.85°E</span>
        </div>
      </div>
    </div>
  );
}
