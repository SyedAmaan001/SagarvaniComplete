import { apiUrl, readApiError } from "../config";

export interface SttResult {
  text: string;
  /** "real" = provider transcription; "mock" = labelled demo text, NOT what the user said */
  mode: "real" | "mock";
  isMock: boolean;
  provider: string;
  status: string;
  warning: string | null;
}

export interface TtsResult {
  mode: "provider" | "browser";
  isProviderAudio: boolean;
  provider: string;
  chunks: string[];
  audioBase64: string[];
  mimeType: string | null;
  warning: string | null;
}

const EXT_BY_TYPE: Record<string, string> = {
  "audio/webm": "webm",
  "video/webm": "webm",
  "audio/ogg": "ogg",
  "audio/mp4": "m4a",
  "audio/mpeg": "mp3",
  "audio/wav": "wav",
  "audio/x-wav": "wav",
};

/** Upload a recorded clip and get the transcript back. */
export async function transcribeAudio(blob: Blob, signal?: AbortSignal): Promise<SttResult> {
  const baseType = (blob.type || "audio/webm").split(";")[0].toLowerCase();
  const form = new FormData();
  form.append("file", blob, `recording.${EXT_BY_TYPE[baseType] || "webm"}`);

  const res = await fetch(apiUrl("/api/orca/stt"), { method: "POST", body: form, signal });
  if (!res.ok) throw new Error(await readApiError(res));
  const d = await res.json();
  return {
    text: d.text,
    mode: d.mode,
    isMock: Boolean(d.is_mock),
    provider: d.provider,
    status: d.status,
    warning: d.warning ?? null,
  };
}

/** Ask the backend how to speak this text (provider audio, or "use browser speech"). */
export async function synthesizeSpeech(text: string, language = "en", signal?: AbortSignal): Promise<TtsResult> {
  const res = await fetch(apiUrl("/api/orca/tts"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
    signal,
  });
  if (!res.ok) throw new Error(await readApiError(res));
  const d = await res.json();
  return {
    mode: d.mode,
    isProviderAudio: Boolean(d.is_provider_audio),
    provider: d.provider,
    chunks: d.chunks || [],
    audioBase64: d.audio_base64 || [],
    mimeType: d.mime_type ?? null,
    warning: d.warning ?? null,
  };
}
