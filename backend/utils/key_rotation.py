"""
Gemini API Key Rotator
Cycles through 3 Gemini keys to avoid per-key rate limits.
"""

import itertools
from utils.gemini import get_gemini_keys

_VALID_KEYS = get_gemini_keys()

_key_cycle = itertools.cycle(_VALID_KEYS)


def get_next_gemini_key() -> str:
    """Return the next Gemini API key in round-robin rotation."""
    if not _VALID_KEYS:
        return ""
    return next(_key_cycle)


def get_all_keys() -> list[str]:
    """Return all available Gemini API keys."""
    return _VALID_KEYS
