import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def get_key_pool(prefix: str, aliases: tuple[str, ...] = ()) -> List[str]:
    """Return unique keys from indexed, comma-separated, and alias settings."""
    values: List[str] = []
    for index in range(1, 21):
        value = os.getenv(f"{prefix}_{index}", "")
        if value:
            values.extend(value.split(","))
    value = os.getenv(prefix, "")
    if value:
        values.extend(value.split(","))
    for alias in aliases:
        value = os.getenv(alias, "")
        if value:
            values.extend(value.split(","))
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))


# ─── Runtime settings (voice / mock mode / CORS / Redis) ──────────────────────

DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    # Deployed Railway frontend (README live-demo URL)
    "https://sagarvani-frontend-production.up.railway.app",
]

_VALID = {
    "STT_MODE": {"auto", "real", "mock"},
    "TTS_MODE": {"auto", "provider", "browser"},
    "DATA_MODE": {"live", "mock"},
}


def _choice(name: str, default: str, warnings: List[str]) -> str:
    raw = os.getenv(name, default).strip().lower() or default
    if raw not in _VALID[name]:
        warnings.append(f"{name}={raw!r} is not one of {sorted(_VALID[name])}; using {default!r}")
        return default
    return raw


def _int(name: str, default: int, warnings: List[str]) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        warnings.append(f"{name}={raw!r} is not a positive integer; using {default}")
        return default


@dataclass
class Settings:
    """Environment-driven configuration. Never holds or exposes secret values."""

    stt_mode: str = "auto"          # auto: real if SARVAM_API_KEY else mock
    tts_mode: str = "auto"          # auto: provider if SARVAM_API_KEY else browser
    data_mode: str = "live"         # live: real feeds only; mock: deterministic labelled demo data
    stt_fallback_to_mock: bool = True
    max_audio_bytes: int = 10 * 1024 * 1024
    max_query_chars: int = 1000
    max_tts_chars: int = 3000
    redis_url: Optional[str] = None
    session_ttl_seconds: int = 3600
    cors_origins: List[str] = field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))
    cors_allow_all: bool = False
    warnings: List[str] = field(default_factory=list)

    @property
    def sarvam_configured(self) -> bool:
        return bool(get_key_pool("SARVAM_API_KEY"))

    @property
    def effective_stt_mode(self) -> str:
        if self.stt_mode == "auto":
            return "real" if self.sarvam_configured else "mock"
        return self.stt_mode

    @property
    def effective_tts_mode(self) -> str:
        if self.tts_mode == "auto":
            return "provider" if self.sarvam_configured else "browser"
        return self.tts_mode

    def public_report(self) -> dict:
        """Safe-to-expose view of configuration (booleans / mode names only)."""
        return {
            "stt_mode": self.effective_stt_mode,
            "tts_mode": self.effective_tts_mode,
            "data_mode": self.data_mode,
            "sarvam_key_configured": self.sarvam_configured,
            "gemini_key_configured": bool(get_key_pool("GEMINI_API_KEY", aliases=("GOOGLE_API_KEY",))),
            "redis_configured": bool(self.redis_url),
            "max_audio_bytes": self.max_audio_bytes,
            "cors_allow_all": self.cors_allow_all,
            "cors_origin_count": len(self.cors_origins),
            "config_warnings": list(self.warnings),
        }


def load_settings() -> Settings:
    """Read + validate settings from the environment (call again after changing env in tests)."""
    warnings: List[str] = []
    s = Settings()
    s.stt_mode = _choice("STT_MODE", "auto", warnings)
    s.tts_mode = _choice("TTS_MODE", "auto", warnings)
    s.data_mode = _choice("DATA_MODE", "live", warnings)
    s.stt_fallback_to_mock = os.getenv("STT_FALLBACK_TO_MOCK", "true").strip().lower() not in ("0", "false", "no")
    s.max_audio_bytes = _int("MAX_AUDIO_BYTES", s.max_audio_bytes, warnings)
    s.max_query_chars = _int("MAX_QUERY_CHARS", s.max_query_chars, warnings)
    s.max_tts_chars = _int("MAX_TTS_CHARS", s.max_tts_chars, warnings)
    s.session_ttl_seconds = _int("SESSION_TTL_SECONDS", s.session_ttl_seconds, warnings)
    s.redis_url = os.getenv("REDIS_URL", "").strip() or None

    raw_origins = os.getenv("CORS_ORIGINS", "").strip()
    if raw_origins == "*":
        s.cors_allow_all = True
    elif raw_origins:
        extra = [o.strip().rstrip("/") for o in raw_origins.split(",") if o.strip()]
        # Explicit origins are *added* to the defaults so a forgotten entry
        # cannot lock out the deployed frontend again.
        s.cors_origins = list(dict.fromkeys(DEFAULT_CORS_ORIGINS + extra))

    if s.stt_mode == "real" and not s.sarvam_configured:
        warnings.append("STT_MODE=real but SARVAM_API_KEY is not set; STT will fail or fall back to mock")
    if s.tts_mode == "provider" and not s.sarvam_configured:
        warnings.append("TTS_MODE=provider but SARVAM_API_KEY is not set; TTS will fall back to browser speech")
    if s.data_mode == "mock":
        warnings.append("DATA_MODE=mock: marine/weather answers use labelled demo data and give no safety recommendations")
    s.warnings = warnings
    return s
