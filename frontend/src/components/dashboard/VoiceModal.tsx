"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Volume2, Sparkles, Check, RefreshCw, X, AlertCircle, Globe, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VoiceState } from "@/lib/types";
import { transcribeAudio, SttResult } from "@/lib/api/voice";
import { stopSpeech } from "@/lib/speech";

interface VoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitTranscript: (query: string) => void;
}

const MAX_RECORD_MS = 30_000;
const MIN_BLOB_BYTES = 1500;
const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  return MIME_CANDIDATES.find((t) => MediaRecorder.isTypeSupported(t));
}

function describeMicError(e: unknown): string {
  const name = e instanceof DOMException ? e.name : "";
  if (name === "NotAllowedError" || name === "SecurityError")
    return "Microphone permission was denied. Allow microphone access in your browser's site settings, then try again.";
  if (name === "NotFoundError") return "No microphone was found on this device.";
  if (name === "NotReadableError") return "The microphone is in use by another application.";
  return e instanceof Error ? e.message : "Could not start recording.";
}

export function VoiceModal({ isOpen, onClose, onSubmitTranscript }: VoiceModalProps) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [transcript, setTranscript] = useState("");
  const [stt, setStt] = useState<SttResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState<number[]>([15, 25, 45, 60, 35, 20, 40]);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const stopTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const cancelledRef = useRef(false);

  const releaseMic = useCallback(() => {
    if (stopTimerRef.current) clearTimeout(stopTimerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
  }, []);

  const teardown = useCallback(() => {
    cancelledRef.current = true;
    abortRef.current?.abort();
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      try { recorderRef.current.stop(); } catch { /* already stopped */ }
    }
    recorderRef.current = null;
    releaseMic();
  }, [releaseMic]);

  const fail = (message: string) => {
    setError(message);
    setVoiceState("error");
  };

  const startListening = useCallback(async () => {
    stopSpeech(); // never record the assistant talking
    cancelledRef.current = false;
    setTranscript("");
    setStt(null);
    setError(null);

    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      fail("This browser does not support microphone recording. Type your question instead, or try a current Chrome, Edge, Firefox or Safari over HTTPS.");
      return;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
    } catch (e) {
      fail(describeMicError(e));
      return;
    }
    if (cancelledRef.current) { stream.getTracks().forEach((t) => t.stop()); return; }
    streamRef.current = stream;

    // real input level for the waveform bars
    try {
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new Ctx();
      audioCtxRef.current = ctx;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      ctx.createMediaStreamSource(stream).connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(data);
        setAudioLevel(Array.from({ length: 7 }, (_, i) => Math.max(8, Math.round((data[i + 1] / 255) * 100))));
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch { /* visualiser is optional */ }

    const mimeType = pickMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    recorderRef.current = recorder;
    chunksRef.current = [];
    recorder.ondataavailable = (ev) => { if (ev.data.size) chunksRef.current.push(ev.data); };
    recorder.onerror = () => { releaseMic(); fail("Recording failed unexpectedly. Please try again."); };
    recorder.onstop = async () => {
      releaseMic();
      if (cancelledRef.current) return;
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || mimeType || "audio/webm" });
      if (blob.size < MIN_BLOB_BYTES) {
        fail("That recording was too short to contain speech. Press the mic and speak for a moment before stopping.");
        return;
      }
      setVoiceState("processing");
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      try {
        const result = await transcribeAudio(blob, ctrl.signal);
        if (cancelledRef.current) return;
        setStt(result);
        setTranscript(result.text);
        setVoiceState("transcript");
      } catch (e) {
        if (cancelledRef.current) return;
        fail(`Could not transcribe the recording: ${e instanceof Error ? e.message : "unknown error"}`);
      }
    };

    recorder.start();
    setVoiceState("listening");
    stopTimerRef.current = setTimeout(() => stopListening(), MAX_RECORD_MS);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [releaseMic]);

  const stopListening = () => {
    const r = recorderRef.current;
    if (r && r.state === "recording") r.stop();
  };

  useEffect(() => {
    if (isOpen) {
      void startListening();
    } else {
      teardown();
      setVoiceState("idle");
    }
    return teardown;
  }, [isOpen, startListening, teardown]);

  const handleRetry = () => {
    teardown();
    void startListening();
  };

  const handleSubmit = () => {
    const q = transcript.trim();
    if (!q) return;
    onSubmitTranscript(q);
    onClose();
  };

  if (!isOpen) return null;

  // Portal to <body>: inside the chat rail the dialog was clipped by the agents rail stacking context.
  return createPortal(
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-lg rounded-2xl border border-border bg-bg-elevated p-6 shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border pb-4 mb-5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-primary">
                <Volume2 className="size-4" />
              </div>
              <div>
                <h3 className="font-heading text-base font-bold text-foreground">Voice Decision Interface</h3>
                <span className="text-[10px] font-mono text-primary">Speech-to-Text · Multilingual</span>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close voice dialog"
              className="rounded-lg p-1.5 text-text-secondary hover:bg-bg-sunken hover:text-foreground transition-colors"
            >
              <X className="size-4" />
            </button>
          </div>

          {/* Language note (the backend auto-detects the spoken language and returns English) */}
          <div className="mb-6 flex items-center gap-2 rounded-xl bg-bg-sunken p-2.5 border border-border text-xs text-text-secondary">
            <Globe className="size-3.5 text-primary shrink-0" />
            <span className="font-mono text-[11px]">Speak in English or an Indian language - it is detected automatically and shown in English.</span>
          </div>

          <div className="min-h-[180px] flex flex-col items-center justify-center text-center p-4">
            {voiceState === "idle" && (
              <p className="text-xs text-text-secondary">Starting microphone...</p>
            )}

            {voiceState === "listening" && (
              <div className="flex flex-col items-center gap-4">
                <div className="relative flex items-center justify-center">
                  <span className="animate-ping absolute inline-flex h-20 w-20 rounded-full bg-primary opacity-30" />
                  <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-primary text-bg-sunken shadow-[0_0_30px_rgba(0,255,255,0.5)]">
                    <Mic className="size-8" />
                  </div>
                </div>
                <div className="flex items-center justify-center gap-1.5 h-10 mt-2" aria-hidden>
                  {audioLevel.map((height, i) => (
                    <motion.div key={i} animate={{ height: `${height}%` }} transition={{ duration: 0.1 }} className="w-1.5 rounded-full bg-primary min-h-[6px]" />
                  ))}
                </div>
                <div>
                  <p className="font-heading text-sm font-semibold text-foreground">Listening...</p>
                  <p className="text-xs text-text-secondary mt-1">Speak your marine question, then press Stop.</p>
                </div>
                <Button type="button" size="sm" onClick={stopListening} className="bg-primary text-bg-sunken font-bold text-xs hover:bg-primary/90">
                  <Square className="size-3.5 mr-1 fill-current" />
                  <span>Stop &amp; Transcribe</span>
                </Button>
              </div>
            )}

            {voiceState === "processing" && (
              <div className="flex flex-col items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-bg-sunken border border-primary/40 text-primary">
                  <RefreshCw className="size-8 animate-spin" />
                </div>
                <p className="font-heading text-sm font-semibold text-foreground">Transcribing...</p>
              </div>
            )}

            {voiceState === "transcript" && stt && (
              <div className="w-full text-left space-y-3">
                <div className="flex items-center justify-between">
                  {stt.isMock ? (
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-warning flex items-center gap-1">
                      <AlertCircle className="size-3" /> Demo transcription - not your speech
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-success flex items-center gap-1">
                      <Check className="size-3" /> Speech transcribed
                    </span>
                  )}
                  <span className="text-[10px] font-mono text-text-secondary">You can edit before submitting</span>
                </div>

                <div className={`rounded-xl border bg-bg-sunken p-3 ${stt.isMock ? "border-warning/50" : "border-primary/40"}`}>
                  <textarea
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    rows={2}
                    aria-label="Recognised question"
                    className="w-full resize-none bg-transparent text-sm text-foreground focus:outline-none leading-relaxed font-medium"
                    placeholder="Transcript text..."
                  />
                </div>

                {stt.warning && (
                  <p className="rounded-lg bg-warning/10 border border-warning/30 p-2.5 text-[11px] text-warning leading-snug">{stt.warning}</p>
                )}
              </div>
            )}

            {voiceState === "error" && (
              <div className="flex flex-col items-center gap-3 text-danger" role="alert">
                <AlertCircle className="size-10" />
                <p className="font-heading text-sm font-semibold">Voice input problem</p>
                <p className="text-xs text-text-secondary max-w-xs">{error}</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="mt-6 border-t border-border pt-4 flex items-center justify-between">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleRetry}
              className="border-border text-text-secondary hover:text-foreground hover:bg-bg-sunken flex items-center gap-1.5 text-xs"
            >
              <RefreshCw className="size-3.5" />
              <span>Record Again</span>
            </Button>

            <div className="flex items-center gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={onClose} className="text-text-secondary hover:text-foreground text-xs">
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                disabled={voiceState !== "transcript" || !transcript.trim()}
                onClick={handleSubmit}
                className="bg-primary text-bg-sunken font-bold text-xs hover:bg-primary/90 shadow-[0_0_15px_rgba(0,255,255,0.2)]"
              >
                <Sparkles className="size-3.5 mr-1" />
                <span>Submit to ORCA</span>
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>,
    document.body
  );
}
