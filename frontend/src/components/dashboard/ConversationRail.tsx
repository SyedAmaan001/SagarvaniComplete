"use client";

import { useState } from "react";
import { ConversationTurn } from "@/lib/types";
import { Send, FileText, FileCheck, Mic, Sparkles, AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, Layers, Volume2, VolumeX, Square } from "lucide-react";
import { useSpeech, speak, stopSpeech, setVoiceReplies } from "@/lib/speech";
import { motion, AnimatePresence } from "framer-motion";
import { VoiceModal } from "./VoiceModal";

interface ConversationRailProps {
  turns: ConversationTurn[];
  onAsk: (q: string, viaVoice?: boolean) => void;
  isTyping: boolean;
  onSelectScenario: (scenarioId: string) => void;
  activeScenarioId?: string;
}

export function ConversationRail({ 
  turns, 
  onAsk, 
  isTyping,
  onSelectScenario,
  activeScenarioId
}: ConversationRailProps) {
  const [inputVal, setInputVal] = useState("");
  const [isVoiceOpen, setIsVoiceOpen] = useState(false);
  const speech = useSpeech();
  const [speakingTurnId, setSpeakingTurnId] = useState<string | null>(null);
  const [expandedEvidence, setExpandedEvidence] = useState<{ [turnId: string]: boolean }>({});

  const toggleEvidence = (turnId: string) => {
    setExpandedEvidence(prev => ({ ...prev, [turnId]: !prev[turnId] }));
  };

  const handleSend = () => {
    if (inputVal.trim()) {
      onAsk(inputVal.trim());
      setInputVal("");
    }
  };

  return (
    <div className="w-[380px] h-full bg-bg-primary border-r border-border flex flex-col shadow-2xl z-20 relative select-none">
      {/* Rail Header */}
      <div className="p-4 border-b border-border bg-bg-elevated/40 flex items-center justify-between">
        <div>
          <span className="font-heading font-bold text-sm text-foreground uppercase tracking-wider block">
            Marine Console
          </span>
          <span className="text-[10px] text-text-secondary font-mono">
            Conversational Intelligence Rail
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => (speech.status === "speaking" || speech.status === "loading" ? stopSpeech() : setVoiceReplies(!speech.voiceReplies))}
            className={`flex items-center gap-1 rounded-md border px-1.5 py-1 text-[10px] font-mono transition-colors ${
              speech.status === "speaking" || speech.status === "loading"
                ? "border-danger/50 text-danger"
                : speech.voiceReplies ? "border-primary/40 text-primary" : "border-border text-text-secondary"
            }`}
            title={speech.status === "speaking" || speech.status === "loading" ? "Stop speaking" : speech.voiceReplies ? "Voice replies on (click to mute)" : "Voice replies muted (click to enable)"}
            aria-label={speech.status === "speaking" || speech.status === "loading" ? "Stop speaking" : speech.voiceReplies ? "Mute voice replies" : "Enable voice replies"}
          >
            {speech.status === "speaking" || speech.status === "loading" ? <Square className="size-3 fill-current" /> : speech.voiceReplies ? <Volume2 className="size-3" /> : <VolumeX className="size-3" />}
            <span>{speech.status === "speaking" ? (speech.kind === "provider" ? "AI voice" : "Browser voice") : speech.status === "loading" ? "..." : speech.voiceReplies ? "Voice on" : "Muted"}</span>
          </button>
          <span className="size-2 rounded-full bg-primary animate-pulse" />
          <span className="font-mono text-[10px] text-primary font-bold">ORCA ACTIVE</span>
        </div>
      </div>

      {/* Preset Demo Quick-Picks */}
      <div className="px-4 py-2.5 bg-bg-sunken border-b border-border/70 flex flex-col gap-1.5">
        <span className="text-[10px] font-mono text-text-secondary uppercase tracking-wider font-semibold">
          Demo Scenarios
        </span>
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => onSelectScenario("safe-fishing-mangalore")}
            className={`px-2.5 py-1 rounded-md text-[11px] font-mono transition-colors ${
              activeScenarioId === "safe-fishing-mangalore"
                ? "bg-primary text-bg-sunken font-bold shadow-sm"
                : "bg-bg-elevated border border-border text-text-secondary hover:text-foreground"
            }`}
          >
            Safe Trip Window
          </button>
          <button
            onClick={() => onSelectScenario("contradiction-squall")}
            className={`px-2.5 py-1 rounded-md text-[11px] font-mono transition-colors ${
              activeScenarioId === "contradiction-squall"
                ? "bg-warning text-bg-sunken font-bold shadow-sm"
                : "bg-bg-elevated border border-border text-warning/90 hover:text-warning"
            }`}
          >
            ⚡ Contradiction Check
          </button>
          <button
            onClick={() => onSelectScenario("pfz-advisory")}
            className={`px-2.5 py-1 rounded-md text-[11px] font-mono transition-colors ${
              activeScenarioId === "pfz-advisory"
                ? "bg-primary text-bg-sunken font-bold shadow-sm"
                : "bg-bg-elevated border border-border text-text-secondary hover:text-foreground"
            }`}
          >
            PFZ & Currents
          </button>
        </div>
      </div>

      {/* Message History Feed */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-5 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent">
        {turns.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 text-text-secondary">
            <div className="w-12 h-12 rounded-2xl bg-bg-elevated border border-border flex items-center justify-center text-primary mb-3 shadow-inner">
              <Sparkles className="size-6" />
            </div>
            <h4 className="font-heading font-semibold text-sm text-foreground mb-1">
              Ask the Ocean a Question
            </h4>
            <p className="text-xs leading-relaxed max-w-[220px]">
              Type a marine query or click the mic button to speak in regional languages.
            </p>
          </div>
        ) : null}

        <AnimatePresence initial={false}>
          {turns.map((turn) => {
            const isUser = turn.role === "user";
            const isExpanded = expandedEvidence[turn.id] ?? false;

            return (
              <motion.div
                key={turn.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex flex-col max-w-[95%] ${isUser ? "self-end" : "self-start"}`}
              >
                {/* User Message Bubble */}
                {isUser ? (
                  <div className="p-3.5 rounded-2xl bg-primary/15 border border-primary/30 text-foreground rounded-br-sm shadow-md">
                    <span className="text-[9px] font-mono text-primary uppercase block mb-1 font-semibold">
                      USER QUERY
                    </span>
                    <p className="text-xs leading-relaxed font-medium">{turn.text}</p>
                    {turn.viaVoice && <span className="text-[9px] font-mono text-text-secondary mt-1 block">via voice</span>}
                  </div>
                ) : (
                  /* Sagarvani System Response Bubble */
                  <div className="p-4 rounded-2xl bg-bg-elevated border border-border text-foreground rounded-bl-sm shadow-xl flex flex-col gap-3">
                    {/* Verdict & Header */}
                    <div className="flex items-center justify-between border-b border-border/60 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="size-2 rounded-full bg-primary" />
                        <span className="font-heading text-xs font-bold tracking-wider text-foreground">
                          SAGARVANI ADVISORY
                        </span>
                      </div>
                      {turn.recommendation?.verdict && (
                        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                          turn.recommendation.verdict === 'SAFE' ? 'bg-success/15 border-success/30 text-success' :
                          turn.recommendation.verdict === 'CAUTION' ? 'bg-warning/15 border-warning/30 text-warning' :
                          'bg-primary/15 border-primary/30 text-primary'
                        }`}>
                          {turn.recommendation.verdict}
                        </span>
                      )}
                    </div>

                    {/* Main Body */}
                    <p className={`text-xs leading-relaxed ${turn.isError ? "text-danger" : "text-text-primary"}`} role={turn.isError ? "alert" : undefined}>
                      {turn.text}
                    </p>

                    {turn.usesMockData && (
                      <p className="rounded-md bg-warning/10 border border-warning/30 px-2 py-1.5 text-[10px] leading-snug text-warning">
                        Not all data here is live: {(turn.mockComponents && turn.mockComponents.join("; ")) || "includes demo or static reference data"}.
                      </p>
                    )}

                    {!turn.isError && (
                      <div className="flex items-center gap-2 text-[10px] font-mono">
                        <button
                          onClick={() => {
                            if (speakingTurnId === turn.id && speech.status !== "idle") { stopSpeech(); setSpeakingTurnId(null); }
                            else { setSpeakingTurnId(turn.id); void speak(turn.text); }
                          }}
                          className="flex items-center gap-1 text-primary hover:underline"
                          aria-label={speakingTurnId === turn.id && speech.status !== "idle" ? "Stop speaking" : "Listen to this answer"}
                        >
                          {speakingTurnId === turn.id && speech.status !== "idle" ? <Square className="size-3 fill-current" /> : <Volume2 className="size-3" />}
                          <span>{speakingTurnId === turn.id && speech.status !== "idle" ? "Stop" : "Listen"}</span>
                        </button>
                        {speakingTurnId === turn.id && speech.message && <span className="text-text-secondary">{speech.message}</span>}
                      </div>
                    )}

                    {/* Evidence Drawer Toggle */}
                    {turn.evidence && turn.evidence.length > 0 && (
                      <div className="pt-2 border-t border-border/50">
                        <button
                          onClick={() => toggleEvidence(turn.id)}
                          className="w-full flex items-center justify-between text-[10px] font-mono text-primary font-semibold hover:underline py-1"
                        >
                          <span className="flex items-center gap-1.5">
                            <FileCheck className="size-3" />
                            <span>Evidence Provenance ({turn.evidence.length} Sources)</span>
                          </span>
                          {isExpanded ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                        </button>

                        {isExpanded && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-2 space-y-2 pl-1"
                          >
                            {turn.evidence.map((ev, i) => (
                              <div
                                key={i}
                                className="rounded-lg bg-bg-sunken border border-border p-2 text-[11px]"
                              >
                                <span className="font-bold text-primary block text-[10px]">
                                  {ev.source}
                                </span>
                                <span className="text-text-secondary text-[10px] leading-tight block mt-0.5">
                                  {ev.summary}
                                </span>
                              </div>
                            ))}
                          </motion.div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            );
          })}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="self-start bg-bg-elevated border border-border rounded-2xl rounded-bl-sm p-3.5 flex gap-2 items-center text-xs text-text-secondary"
            >
              <div className="flex gap-1 items-center">
                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="font-mono text-[10px]">ORCA is fusing agent evidence...</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input Box & Voice Trigger */}
      <div className="p-3.5 border-t border-border bg-bg-primary">
        <div className="relative flex items-center">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Ask Sagarvani about sea conditions..."
            className="w-full bg-bg-elevated border border-border rounded-full pl-4 pr-20 py-2.5 text-xs text-foreground focus:outline-none focus:border-primary/50 transition-colors placeholder:text-muted-foreground"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSend();
            }}
          />

          <div className="absolute right-2 flex items-center gap-1">
            {/* Voice Mic Button */}
            <button
              onClick={() => setIsVoiceOpen(true)}
              className="w-7 h-7 rounded-full flex items-center justify-center text-primary hover:bg-bg-sunken hover:scale-105 transition-all shadow-sm"
              title="Voice Input (BHASHINI Multilingual)"
              aria-label="Activate voice query"
            >
              <Mic className="w-3.5 h-3.5" />
            </button>

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={!inputVal.trim()}
              className="w-7 h-7 rounded-full bg-primary text-bg-sunken flex items-center justify-center hover:bg-primary/90 disabled:opacity-40 disabled:hover:bg-primary transition-colors"
              aria-label="Send message"
            >
              <Send className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Voice Modal for Speech MVP */}
      <VoiceModal
        isOpen={isVoiceOpen}
        onClose={() => setIsVoiceOpen(false)}
        onSubmitTranscript={(q) => onAsk(q, true)}
      />
    </div>
  );
}
