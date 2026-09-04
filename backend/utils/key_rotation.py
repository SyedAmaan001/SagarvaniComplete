"""
Gemini API Key Rotator
Cycles through 3 Gemini keys to avoid per-key rate limits.
"""

import os
import itertools
from dotenv import load_dotenv

load_dotenv()

_GEMINI_KEYS = [os.getenv(f"GEMINI_API_KEY_{i}", "") for i in range(1, 11)]
# Filter out empty keys
_VALID_KEYS = [k.strip() for k in _GEMINI_KEYS if k and k.strip()]

if not _VALID_KEYS:
    raise EnvironmentError("No valid GEMINI_API_KEY_* found in .env")

_key_cycle = itertools.cycle(_VALID_KEYS)


def get_next_gemini_key() -> str:
    """Return the next Gemini API key in round-robin rotation."""
    return next(_key_cycle)


def get_all_keys() -> list[str]:
    """Return all available Gemini API keys."""
    return _VALID_KEYS
