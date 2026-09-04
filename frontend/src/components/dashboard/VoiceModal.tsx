"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Volume2, Sparkles, Check, RefreshCw, X, AlertCircle, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VoiceState, LanguageCode } from "@/lib/types";

interface VoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitTranscript: (query: string) => void;
}

const LANGUAGES: { code: LanguageCode; name: string; nativeName: string; sampleQuery: string }[] = [
  { 
    code: "kn", 
    name: "Kannada", 
    nativeName: "ಕನ್ನಡ", 
    sampleQuery: "ಮಂಗಳೂರು ಸಮೀಪ ನಾಳೆ ಬೆಳಿಗ್ಗೆ 11 ಮೀಟರ್ ಬೋಟು ಮೀನುಗಾರಿಕೆಗೆ ತೆಗೆದುಕೊಂಡು ಹೋಗಬಹುದಾ?" 
  },
  { 
    code: "en", 
    name: "English", 
    nativeName: "English", 
    sampleQuery: "Is it safe for an 11-meter boat to fish 15 nautical miles off Mangalore Port tomorrow morning?" 
  },
  { 
    code: "hi", 
    name: "Hindi", 
    nativeName: "हिन्दी", 
    sampleQuery: "क्या कल सुबह मैंगलोर तट से 15 नॉटिकल मील दूर मछली पकड़ने जाना सुरक्षित है?" 
  },
  { 
    code: "ta", 
    name: "Tamil", 
    nativeName: "தமிழ்", 
    sampleQuery: "மங்களூர் துறைமுகத்தில் இருந்து நாளை காலை படகு எடுத்து செல்லலாமா?" 
  },
  { 
    code: "te", 
    name: "Telugu", 
    nativeName: "తెలుగు", 
    sampleQuery: "రేపు ఉదయం మంగళూరు తీరంలో చేపల వేటకు వెళ్లడం సురక్షితమేనా?" 
  },
  { 
    code: "ml", 
    name: "Malayalam", 
    nativeName: "മലയാളം", 
    sampleQuery: "നാളെ രാവിലെ മംഗലാപുരം തീരത്ത് ബോട്ട് ഇറക്കുന്നത് സുരക്ഷിതമാണോ?" 
  },
];

export function VoiceModal({ isOpen, onClose, onSubmitTranscript }: VoiceModalProps) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [selectedLang, setSelectedLang] = useState<LanguageCode>("kn");
  const [transcript, setTranscript] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [audioLevel, setAudioLevel] = useState<number[]>([15, 25, 45, 60, 35, 20, 40]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Audio wave animation during listening
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (voiceState === "listening") {
      interval = setInterval(() => {
        setAudioLevel([
          Math.floor(Math.random() * 60) + 15,
          Math.floor(Math.random() * 85) + 20,
          Math.floor(Math.random() * 100) + 30,
          Math.floor(Math.random() * 90) + 25,
          Math.floor(Math.random() * 70) + 20,
          Math.floor(Math.random() * 80) + 20,
          Math.floor(Math.random() * 50) + 15,
        ]);
      }, 100);
    }
    return () => clearInterval(interval);
  }, [voiceState]);

  // Reset when opened
  useEffect(() => {
    if (isOpen) {
      startListening();
    } else {
      if (timerRef.current) clearTimeout(timerRef.current);
      setVoiceState("idle");
    }
  }, [isOpen]);

  const startListening = () => {
    setVoiceState("listening");
    setTranscript("");
    setTranslatedText("");

    const currentLangObj = LANGUAGES.find((l) => l.code === selectedLang) || LANGUAGES[0];

    // Simulate speech-to-text with BHASHINI multilingual pipeline
    timerRef.current = setTimeout(() => {
      setVoiceState("processing");
      
      timerRef.current = setTimeout(() => {
        setVoiceState("transcript");
        setTranscript(currentLangObj.sampleQuery);
        if (selectedLang !== "en") {
          setTranslatedText("Is it safe for an 11-meter boat to fish 15 nautical miles off Mangalore Port tomorrow morning?");
        }
      }, 1200);
    }, 2800);
  };

  const handleRetry = () => {
    startListening();
  };

  const handleSubmit = () => {
    if (!transcript.trim()) return;
    const finalQuery = translatedText ? `${transcript} (${translatedText})` : transcript;
    onSubmitTranscript(finalQuery);
    onClose();
  };

  if (!isOpen) return null;

  const currentLangObj = LANGUAGES.find((l) => l.code === selectedLang) || LANGUAGES[0];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
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
                <h3 className="font-heading text-base font-bold text-foreground">
                  Voice Decision Interface
                </h3>
                <span className="text-[10px] font-mono text-primary">
                  BHASHINI · Multilingual Speech-to-Text MVP
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-text-secondary hover:bg-bg-sunken hover:text-foreground transition-colors"
            >
              <X className="size-4" />
            </button>
          </div>

          {/* Language Selector */}
          <div className="mb-6 flex items-center justify-between gap-2 rounded-xl bg-bg-sunken p-2.5 border border-border">
            <div className="flex items-center gap-1.5 text-xs text-text-secondary">
              <Globe className="size-3.5 text-primary" />
              <span className="font-mono text-[11px]">Speech Language:</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => {
                    setSelectedLang(lang.code);
                    if (voiceState === "transcript") {
                      setTranscript(lang.sampleQuery);
                      if (lang.code !== "en") {
                        setTranslatedText("Is it safe for an 11-meter boat to fish 15 nautical miles off Mangalore Port tomorrow morning?");
                      } else {
                        setTranslatedText("");
                      }
                    }
                  }}
                  className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors ${
                    selectedLang === lang.code
                      ? "bg-primary text-bg-sunken font-bold"
                      : "text-text-secondary hover:bg-bg-elevated hover:text-foreground"
                  }`}
                >
                  {lang.nativeName}
                </button>
              ))}
            </div>
          </div>

          {/* Main State Canvas */}
          <div className="min-h-[180px] flex flex-col items-center justify-center text-center p-4">
            {/* 1. Listening State */}
            {voiceState === "listening" && (
              <div className="flex flex-col items-center gap-4">
                <div className="relative flex items-center justify-center">
                  <span className="animate-ping absolute inline-flex h-20 w-20 rounded-full bg-primary opacity-30" />
                  <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-primary text-bg-sunken shadow-[0_0_30px_rgba(0,255,255,0.5)]">
                    <Mic className="size-8" />
                  </div>
                </div>

                {/* Animated Waveform Bars */}
                <div className="flex items-center justify-center gap-1.5 h-10 mt-2">
                  {audioLevel.map((height, i) => (
                    <motion.div
                      key={i}
                      animate={{ height: `${height}%` }}
                      transition={{ duration: 0.1 }}
                      className="w-1.5 rounded-full bg-primary min-h-[6px]"
                    />
                  ))}
                </div>

                <div>
                  <p className="font-heading text-sm font-semibold text-foreground">
                    Listening in {currentLangObj.name} ({currentLangObj.nativeName})...
                  </p>
                  <p className="text-xs text-text-secondary mt-1">
                    Speak your marine question naturally.
                  </p>
                </div>
              </div>
            )}

            {/* 2. Processing State */}
            {voiceState === "processing" && (
              <div className="flex flex-col items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-bg-sunken border border-primary/40 text-primary">
                  <RefreshCw className="size-8 animate-spin" />
                </div>
                <div>
                  <p className="font-heading text-sm font-semibold text-foreground">
                    Transcribing & Parsing Intent...
                  </p>
                  <p className="text-xs text-text-secondary mt-1">
                    BHASHINI acoustic model aligning phonemes to marine terminology.
                  </p>
                </div>
              </div>
            )}

            {/* 3. Transcript State (Editable & Confirmable) */}
            {voiceState === "transcript" && (
              <div className="w-full text-left space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-success flex items-center gap-1">
                    <Check className="size-3" /> Speech Transcribed
                  </span>
                  <span className="text-[10px] font-mono text-text-secondary">
                    You can edit before submitting
                  </span>
                </div>

                <div className="rounded-xl border border-primary/40 bg-bg-sunken p-3">
                  <textarea
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    rows={2}
                    className="w-full resize-none bg-transparent text-sm text-foreground focus:outline-none leading-relaxed font-medium"
                    placeholder="Transcript text..."
                  />
                </div>

                {translatedText && (
                  <div className="rounded-lg bg-bg-elevated/80 border border-border p-2.5 text-xs text-text-secondary">
                    <span className="text-[9px] font-mono uppercase text-primary block mb-0.5">ORCA Normalized Intent (English):</span>
                    <p className="italic text-foreground/90">{translatedText}</p>
                  </div>
                )}
              </div>
            )}

            {/* 4. Error State */}
            {voiceState === "error" && (
              <div className="flex flex-col items-center gap-3 text-danger">
                <AlertCircle className="size-10" />
                <p className="font-heading text-sm font-semibold">Microphone Audio Not Detected</p>
                <p className="text-xs text-text-secondary max-w-xs">
                  Please check browser microphone permissions or retry.
                </p>
              </div>
            )}
          </div>

          {/* Footer Controls */}
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
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-text-secondary hover:text-foreground text-xs"
              >
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                disabled={voiceState === "listening" || voiceState === "processing" || !transcript.trim()}
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
    </AnimatePresence>
  );
}
