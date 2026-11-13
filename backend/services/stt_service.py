"""
Speech-to-text service.

Real mode  -> Sarvam AI (existing integration in agents/interpreter_agent.py).
Mock mode  -> deterministic, clearly labelled demo transcript. It does NOT
              recognise speech; it only keeps the voice flow demonstrable when no
              provider key is configured (or the provider is down and fallback is on).
"""

import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

from utils.config import Settings

logger = logging.getLogger("sagarvani.stt")

MIN_AUDIO_BYTES = 256

ALLOWED_AUDIO_TYPES = {
    "audio/webm", "video/webm", "audio/ogg", "audio/opus", "application/ogg",
    "audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave",
    "audio/mpeg", "audio/mp3", "audio/mp4", "audio/x-m4a", "audio/m4a", "audio/aac",
    "audio/flac", "audio/x-flac",
}
ALLOWED_EXTENSIONS = {".webm", ".ogg", ".opus", ".wav", ".mp3", ".mp4", ".m4a", ".aac", ".flac"}

MOCK_TRANSCRIPTS = [
    "Hello Sagarvani, what can you do?",
    "What is the weather like near Malpe?",
    "Should fishermen go to sea today?",
    "What are the wave conditions near Mangalore?",
]


class AudioValidationError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class STTError(Exception):
    """Real STT provider failed and fallback to mock is disabled."""


@dataclass
class STTResult:
    text: str
    mode: str            # real | mock
    provider: str
    status: str          # ok | fallback_to_mock
    bytes_received: int
    duration_sec_estimate: Optional[float] = None
    warning: Optional[str] = None

    @property
    def is_mock(self) -> bool:
        return self.mode == "mock"


def normalize_content_type(content_type: Optional[str]) -> str:
    return (content_type or "").split(";")[0].strip().lower()


def validate_audio(filename: Optional[str], content_type: Optional[str], data: bytes, settings: Settings) -> str:
    """Return the normalised content type or raise AudioValidationError."""
    size = len(data)
    if size == 0:
        raise AudioValidationError(422, "empty_audio", "The uploaded audio file is empty.")
    if size < MIN_AUDIO_BYTES:
        raise AudioValidationError(422, "audio_too_short", "The recording is too short to contain speech. Hold the mic a little longer.")
    if size > settings.max_audio_bytes:
        raise AudioValidationError(
            413, "audio_too_large",
            f"Audio is {size} bytes; the limit is {settings.max_audio_bytes} bytes.",
        )
    ctype = normalize_content_type(content_type)
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if filename and "." in filename else ""
    type_ok = ctype in ALLOWED_AUDIO_TYPES
    generic_ok = ctype in ("", "application/octet-stream") and ext in ALLOWED_EXTENSIONS
    if not (type_ok or generic_ok):
        raise AudioValidationError(
            415, "unsupported_audio_type",
            f"Unsupported audio type {ctype or 'unknown'!r}. Use webm, ogg, wav, mp3, mp4/m4a, aac or flac.",
        )
    return ctype or "audio/wav"


def mock_transcript(data: bytes) -> str:
    """Deterministic pick (same audio -> same text) so tests are repeatable."""
    return MOCK_TRANSCRIPTS[hashlib.sha256(data).digest()[0] % len(MOCK_TRANSCRIPTS)]


def transcribe(data: bytes, filename: Optional[str], content_type: str, settings: Settings) -> STTResult:
    size = len(data)
    mode = settings.effective_stt_mode

    if mode == "real":
        from agents.interpreter_agent import transcribe_and_translate_audio

        text, stats = transcribe_and_translate_audio(data, filename or "recording.webm", content_type)
        if text and text.strip():
            return STTResult(
                text=text.strip(), mode="real", provider="sarvam:" + str(stats.get("model", "saaras")),
                status="ok", bytes_received=size, duration_sec_estimate=None,
            )
        reason = str(stats.get("status", "no transcript returned"))
        logger.error("Real STT failed: %s", reason)
        if not settings.stt_fallback_to_mock:
            raise STTError(f"Speech recognition failed: {reason}")
        return STTResult(
            text=mock_transcript(data), mode="mock", provider="mock", status="fallback_to_mock",
            bytes_received=size,
            warning=f"Real speech recognition failed ({reason}). This is DEMO text, not what you said - please edit it or type your question.",
        )

    return STTResult(
        text=mock_transcript(data), mode="mock", provider="mock", status="ok", bytes_received=size,
        warning="Demo transcription: no speech-to-text provider is configured (set SARVAM_API_KEY). This is NOT what you said - edit it or type your question.",
    )
