"""
Text-to-speech service.

provider mode -> Sarvam AI Bulbul TTS (same SARVAM_API_KEY as STT), returns base64 audio.
browser mode  -> returns only the text chunks; the frontend speaks them with the
                 browser's speechSynthesis. The response says so explicitly.

If the provider fails we degrade to browser mode and include the reason.
Verified against the live Sarvam API (text + target_language_code, provider-default model).
"""

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests

from utils.config import Settings, get_key_pool

logger = logging.getLogger("sagarvani.tts")

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
# Model and speaker are optional overrides: Sarvam retires model names (bulbul:v2 now
# returns 400 "deprecated"), so by default we let the provider choose its current model.
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "").strip()
SARVAM_TTS_SPEAKER = os.getenv("SARVAM_TTS_SPEAKER", "").strip()
MAX_CHUNK_CHARS = 450

LANG_CODES: Dict[str, str] = {
    "en": "en-IN", "hi": "hi-IN", "kn": "kn-IN", "ta": "ta-IN", "te": "te-IN",
    "ml": "ml-IN", "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN", "or": "od-IN", "pa": "pa-IN",
}


@dataclass
class TTSResult:
    mode: str                      # provider | browser
    provider: str
    language: str
    chunks: List[str]
    audio_base64: List[str] = field(default_factory=list)
    mime_type: Optional[str] = None
    warning: Optional[str] = None

    @property
    def is_provider_audio(self) -> bool:
        return self.mode == "provider" and bool(self.audio_base64)


# Emoji, dingbats, bullets and variation selectors (built from code points, not literals)
_SYMBOLS = re.compile(
    "[" + chr(0x1F000) + "-" + chr(0x10FFFF) + chr(0x2022)
    + chr(0x2600) + "-" + chr(0x27BF) + chr(0x2B00) + "-" + chr(0x2BFF) + chr(0xFE0F) + "]"
)


def clean_for_speech(text: str) -> str:
    """Strip markdown/emoji/bullets that sound wrong when read aloud."""
    text = re.sub(r"[*_`#>]+", "", text)
    text = _SYMBOLS.sub("", text)
    text = re.sub(r"^\s*-\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", text).strip()


def split_into_chunks(text: str, limit: int = MAX_CHUNK_CHARS) -> List[str]:
    """Split on sentence boundaries so long answers become several short utterances."""
    text = clean_for_speech(text)
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?।])\s+", text)
    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        while len(sentence) > limit:  # very long sentence: hard split on spaces
            cut = sentence.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if len(current) + len(sentence) + 1 > limit and current:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def _provider_call(chunk: str, lang_code: str, voice: Optional[str], key: str) -> str:
    body = {"text": chunk, "target_language_code": lang_code}
    if voice or SARVAM_TTS_SPEAKER:
        body["speaker"] = voice or SARVAM_TTS_SPEAKER
    if SARVAM_TTS_MODEL:
        body["model"] = SARVAM_TTS_MODEL
    resp = requests.post(
        SARVAM_TTS_URL,
        headers={"api-subscription-key": key, "Content-Type": "application/json"},
        json=body,
        timeout=20,
    )
    resp.raise_for_status()
    audios = resp.json().get("audios") or []
    if not audios:
        raise RuntimeError("provider returned no audio")
    return audios[0]


def synthesize(text: str, language: str, voice: Optional[str], settings: Settings) -> TTSResult:
    language = (language or "en").lower()
    chunks = split_into_chunks(text)
    if not chunks:
        raise ValueError("Nothing to speak after cleaning the text.")

    if settings.effective_tts_mode != "provider":
        return TTSResult(mode="browser", provider="browser-speechSynthesis", language=language, chunks=chunks)

    keys = get_key_pool("SARVAM_API_KEY")
    if not keys:
        return TTSResult(
            mode="browser", provider="browser-speechSynthesis", language=language, chunks=chunks,
            warning="SARVAM_API_KEY is not set; using browser speech.",
        )

    lang_code = LANG_CODES.get(language, "en-IN")
    audio: List[str] = []
    last_error = ""
    for key in keys:
        try:
            audio = [_provider_call(c, lang_code, voice, key) for c in chunks]
            break
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            logger.error("Provider TTS failed with one key: %s", last_error)
            audio = []
    if audio:
        return TTSResult(
            mode="provider", provider=f"sarvam:{SARVAM_TTS_MODEL or 'default'}", language=language,
            chunks=chunks, audio_base64=audio, mime_type="audio/wav",
        )
    return TTSResult(
        mode="browser", provider="browser-speechSynthesis", language=language, chunks=chunks,
        warning=f"Provider speech failed ({last_error}); falling back to browser speech.",
    )
