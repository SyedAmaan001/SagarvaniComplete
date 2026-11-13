from typing import Any

from utils.config import get_key_pool


try:
    from google import genai as _modern_genai
except ImportError:
    _modern_genai = None

try:
    import google.generativeai as _legacy_genai
except ImportError:
    _legacy_genai = None


GEMINI_AVAILABLE = _modern_genai is not None or _legacy_genai is not None


def get_gemini_keys() -> list[str]:
    return get_key_pool("GEMINI_API_KEY", aliases=("GOOGLE_API_KEY",))


def generate_text(api_key: str, model: str, prompt: str) -> str:
    """Generate text through either supported Google SDK."""
    if _modern_genai is not None:
        client = _modern_genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text or ""

    if _legacy_genai is not None:
        _legacy_genai.configure(api_key=api_key)
        response = _legacy_genai.GenerativeModel(model).generate_content(prompt)
        return response.text or ""

    raise RuntimeError("No supported Google Gemini SDK is installed")
