"use client";

import { Alert } from "@/lib/types";
import { AlertTriangle, AlertCircle, Info, MapPin } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AlertsPanelProps {
  alerts: Alert[];
  onFocusAlert?: (coords: [number, number]) => void;
}

export function AlertsPanel({ alerts, onFocusAlert }: AlertsPanelProps) {
  if (alerts.length === 0) return null;

  return (
    <div className="absolute top-4 left-4 z-20 w-full max-w-sm flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {alerts.map((alert) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, y: -15, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border backdrop-blur-xl shadow-2xl transition-all ${
              alert.type === 'danger' ? 'bg-danger/15 border-danger/40 text-foreground' :
              alert.type === 'warning' ? 'bg-warning/15 border-warning/40 text-foreground' :
              'bg-primary/15 border-primary/40 text-foreground'
            }`}
          >
            <div className="mt-0.5 shrink-0">
              {alert.type === 'danger' && <AlertTriangle className="w-4 h-4 text-danger animate-pulse" />}
              {alert.type === 'warning' && <AlertCircle className="w-4 h-4 text-warning" />}
              {alert.type === 'info' && <Info className="w-4 h-4 text-primary" />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-heading font-bold text-xs leading-none">
                  {alert.title}
                </span>
                <span className="text-[9px] font-mono text-text-secondary shrink-0">
                  {alert.timestamp}
                </span>
              </div>
              <p className="text-[11px] text-text-secondary leading-relaxed mb-2">
                {alert.message}
              </p>
              <div className="flex items-center justify-between text-[10px] font-mono text-text-secondary pt-1 border-t border-border/40">
                <span>Source: {alert.source}</span>
                {alert.coordinates && onFocusAlert && (
                  <button
                    onClick={() => onFocusAlert(alert.coordinates!)}
                    className="text-primary hover:underline flex items-center gap-1 font-bold"
                  >
                    <MapPin className="size-2.5" /> Locate
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
