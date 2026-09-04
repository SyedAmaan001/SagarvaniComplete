"use client";

import { motion, AnimatePresence } from "framer-motion";
import { GitCommit, FileCheck, ShieldCheck, X, Sparkles, Layers } from "lucide-react";

interface ReasoningPanelProps {
  isOpen: boolean;
  onClose: () => void;
  trace: string[];
  intent?: string;
  isContradiction?: boolean;
}

export function ReasoningPanel({ isOpen, onClose, trace, intent, isContradiction }: ReasoningPanelProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, x: 20, y: 10 }}
          animate={{ opacity: 1, x: 0, y: 0 }}
          exit={{ opacity: 0, x: 20, y: 10 }}
          className="absolute bottom-6 right-6 w-96 bg-bg-elevated/95 border border-border rounded-2xl shadow-2xl overflow-hidden z-30 backdrop-blur-xl"
        >
          {/* Header */}
          <div className="bg-bg-primary/80 border-b border-border p-3.5 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <ShieldCheck className="size-4 text-primary" />
              <span className="text-xs font-heading font-bold text-foreground uppercase tracking-wider">
                ORCA Reasoning & Validation Trace
              </span>
            </div>
            <button 
              onClick={onClose} 
              className="text-text-secondary hover:text-foreground p-1 rounded-md hover:bg-bg-sunken transition-colors"
              aria-label="Close reasoning panel"
            >
              <X className="size-4" />
            </button>
          </div>

          {/* Intent Card */}
          {intent && (
            <div className="px-4 py-2.5 bg-bg-sunken/60 border-b border-border/60 text-xs">
              <span className="text-[10px] font-mono text-primary uppercase font-bold block mb-0.5">
                Target Intent:
              </span>
              <p className="text-text-secondary text-[11px] leading-tight font-medium">
                {intent}
              </p>
            </div>
          )}
          
          {/* Step-by-Step Chain of Thought */}
          <div className="p-4 max-h-72 overflow-y-auto flex flex-col gap-3 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent font-mono text-xs">
            {trace.map((step, idx) => {
              const isLast = idx === trace.length - 1;
              const isConflictStep = step.includes("CONTRADICTION") || step.includes("RE-PLANNING");

              return (
                <div key={idx} className="flex gap-2.5 relative">
                  {!isLast && (
                    <div className="absolute left-[8px] top-5 bottom-[-12px] w-0.5 bg-border" />
                  )}
                  <div className={`relative z-10 w-4 h-4 rounded-full border flex items-center justify-center shrink-0 mt-0.5 ${
                    isLast ? "bg-success/20 border-success text-success" :
                    isConflictStep ? "bg-warning/20 border-warning text-warning" :
                    "bg-bg-sunken border-border text-primary"
                  }`}>
                    {isLast ? (
                      <FileCheck className="size-2.5" />
                    ) : (
                      <GitCommit className="size-2.5" />
                    )}
                  </div>
                  <p className={`text-[11px] leading-relaxed pt-0.5 ${
                    isConflictStep ? "text-warning font-semibold" :
                    isLast ? "text-success font-semibold" :
                    "text-text-secondary"
                  }`}>
                    {step}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Validation Status Bar */}
          <div className="p-3 bg-bg-sunken border-t border-border flex items-center justify-between text-[10px] font-mono">
            <span className="text-text-secondary">Validation Engine:</span>
            <span className={`font-bold ${isContradiction ? "text-warning" : "text-success"}`}>
              {isContradiction ? "RESOLVED VIA SATELLITE RE-CHECK" : "100% CROSS-CHECK VERIFIED"}
            </span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
