"""
ORCA - Marine EcOsystem Reasoning with Collaborative Agents
Stage 1: Access & Understanding Layer

Pipeline:
    User Query - TEXT (any Indian language)
        -> Sarvam AI Text Translation      (-> English)
        -> LangChain + Google Gemini Structured Extraction (-> MarineIntentSchema)

    User Query - VOICE (any Indian regional language, via microphone)
        -> Sarvam AI Speech-to-Text-Translate (-> English transcript, single call)
        -> LangChain + Google Gemini Structured Extraction (-> MarineIntentSchema)

    Both paths converge on the same MarineIntentSchema JSON payload,
    which is handed off to the Stage 2 Orchestrator.

Compatible with Google Antigravity IDE. Run with:
    streamlit run app.py

Required environment variables:
    SARVAM_API_KEY   - Sarvam AI API key
    GOOGLE_API_KEY   - Google AI Studio / Gemini API key(s). Single key, or comma-separated
                       list of fallback keys (e.g. "key1,key2,key3") for automatic rotation
                       on rate-limit/quota errors via KeyRotator.
"""

import io
import os
from typing import Optional
import wave

import requests
import streamlit as st
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI


# --------------------------------------------------------------------------
# 1. CONFIGURATION & MODEL REGISTRY
# --------------------------------------------------------------------------

SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_TRANSLATE_MODEL = "mayura:v1"
SARVAM_STT_MODEL = "saaras:v3"

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY") or getattr(st, "secrets", {}).get("SARVAM_API_KEY", "")
GOOGLE_API_KEY_RAW = os.environ.get("GOOGLE_API_KEY") or getattr(st, "secrets", {}).get("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL") or getattr(st, "secrets", {}).get("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_DAILY_TOKEN_QUOTA = int(os.environ.get("GEMINI_DAILY_TOKEN_QUOTA") or getattr(st, "secrets", {}).get("GEMINI_DAILY_TOKEN_QUOTA", 1000000))
SARVAM_CHAR_QUOTA = int(os.environ.get("SARVAM_CHAR_QUOTA") or getattr(st, "secrets", {}).get("SARVAM_CHAR_QUOTA", 500000))
SARVAM_AUDIO_QUOTA_SEC = float(os.environ.get("SARVAM_AUDIO_QUOTA_SEC") or getattr(st, "secrets", {}).get("SARVAM_AUDIO_QUOTA_SEC", 3600.0))

st.set_page_config(page_title="ORCA - Stage 1: Access & Understanding", page_icon="🐋")


class KeyRotator:
    """
    Tracks a pool of Gemini API keys (parsed from a comma-separated string)
    and rotates to the next one when the active key hits a rate-limit /
    quota-exhaustion error. Lightweight, in-memory, no external deps.
    """

    def __init__(self, keys_csv: str):
        self.keys = [k.strip() for k in keys_csv.split(",") if k.strip()]
        if not self.keys:
            raise ValueError(
                "No GOOGLE_API_KEY(s) found. Set GOOGLE_API_KEY to a single "
                "key, or a comma-separated list of fallback keys."
            )
        self.index = 0

    @property
    def current_key(self) -> str:
        return self.keys[self.index]

    def rotate(self) -> bool:
        """Advance to the next key. Returns False once every key is exhausted."""
        if self.index + 1 >= len(self.keys):
            return False
        self.index += 1
        return True


key_rotator = KeyRotator(GOOGLE_API_KEY_RAW)
sarvam_key_rotator = KeyRotator(SARVAM_API_KEY)


def _is_quota_error(exc: Exception) -> bool:
    """
    Loosely detect rate-limit / quota-exhaustion errors across Gemini SDK
    versions, without a hard dependency on a specific exception class
    (e.g. google.api_core.exceptions.ResourceExhausted).
    """
    exc_name = type(exc).__name__.lower()
    exc_msg = str(exc).lower()
    return (
        "resourceexhausted" in exc_name
        or "429" in exc_msg
        or "quota" in exc_msg
        or "rate limit" in exc_msg
        or "resource_exhausted" in exc_msg
    )


# --------------------------------------------------------------------------
# 2. PYDANTIC SCHEMA - the contract handed off to the Stage 2 Orchestrator
# --------------------------------------------------------------------------

class MarineIntentSchema(BaseModel):
    """Structured representation of a fisherman/user's marine query intent."""

    intent_type: str = Field(
        description=(
            "The core intent of the query. Must be one of: "
            "find_pfz, weather_alert, safe_route, geofence_check, general_query."
        )
    )
    location: Optional[str] = Field(
        default=None,
        description="Named location, coordinates, or region mentioned in the query, if any."
    )
    date: Optional[str] = Field(
        default=None,
        description="Date or time reference mentioned in the query (e.g., 'today', 'tomorrow', '15 Aug'), if any."
    )
    vessel_type: Optional[str] = Field(
        default=None,
        description="Type of vessel mentioned, e.g., trawler, gillnetter, canoe, if any."
    )


# --------------------------------------------------------------------------
# 3. SARVAM AI - TEXT TRANSLATION (for the typed chat_input path)
# --------------------------------------------------------------------------

def translate_to_english(text: str) -> tuple[str, dict]:
    """
    Translate a typed user query from any supported Indian language into
    standard English using the Sarvam AI Translate API (model: mayura:v1).
    Supports automatic fallback rotation across available Sarvam API keys.

    Returns tuple: (translated_english_text, sarvam_stats_dict).
    """
    char_count = len(text)
    if not SARVAM_API_KEY:
        st.warning("SARVAM_API_KEY not set. Skipping translation and using raw input.")
        return text, {"model": SARVAM_TRANSLATE_MODEL, "chars": char_count, "status": "skipped"}

    while True:
        headers = {
            "api-subscription-key": sarvam_key_rotator.current_key,
            "Content-Type": "application/json",
        }

        payload = {
            "input": text,
            "source_language_code": "auto",   # auto-detect the input language
            "target_language_code": "en-IN",  # translate to Indian English
            "mode": "formal",
            "model": SARVAM_TRANSLATE_MODEL,
        }

        try:
            response = requests.post(SARVAM_TRANSLATE_URL, headers=headers, json=payload, timeout=15)
            if response.status_code in (429, 403, 500, 502, 503) and sarvam_key_rotator.rotate():
                st.warning(f"Sarvam key #{sarvam_key_rotator.index} hit an error — rotating to key #{sarvam_key_rotator.index + 1}.")
                continue

            response.raise_for_status()
            data = response.json()
            translated = data.get("translated_text", text)

            stats = {
                "model": SARVAM_TRANSLATE_MODEL,
                "chars": char_count,
                "status": "success",
            }

            if hasattr(st, "session_state"):
                st.session_state.sarvam_translate_calls = (
                    st.session_state.get("sarvam_translate_calls", 0) + 1
                )
                st.session_state.sarvam_translate_chars = (
                    st.session_state.get("sarvam_translate_chars", 0) + char_count
                )

            return translated, stats
        except requests.exceptions.RequestException as e:
            if sarvam_key_rotator.rotate():
                st.warning(f"Sarvam translation error ({e}) — rotating to key #{sarvam_key_rotator.index + 1} and retrying.")
                continue
            st.error(f"Sarvam AI translation failed on all keys, using original text. Error: {e}")
            return text, {"model": SARVAM_TRANSLATE_MODEL, "chars": char_count, "status": f"failed: {e}"}


# --------------------------------------------------------------------------
# 4. SARVAM AI - SPEECH-TO-TEXT-TRANSLATE (for the microphone / st.audio_input path)
# --------------------------------------------------------------------------

def _get_audio_metadata(audio_file) -> tuple[float, int]:
    """Calculate audio duration in seconds and file size in bytes."""
    try:
        audio_file.seek(0)
        audio_bytes = audio_file.read()
        byte_len = len(audio_bytes)
        audio_file.seek(0)

        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate) if rate > 0 else 0.0
            return round(duration, 2), byte_len
    except Exception:
        audio_file.seek(0, os.SEEK_END)
        size = audio_file.tell()
        audio_file.seek(0)
        return round(size / 88200.0, 1), size


def transcribe_and_translate_audio(audio_file) -> tuple[Optional[str], dict]:
    """
    Send recorded audio (any Indian regional language) to Sarvam AI's
    speech-to-text-translate endpoint (model: saaras:v3).
    Supports automatic fallback rotation across available Sarvam API keys.

    Returns tuple: (english_transcript, sarvam_stats_dict).
    """
    duration_sec, audio_bytes_len = _get_audio_metadata(audio_file)

    if not SARVAM_API_KEY:
        st.warning("SARVAM_API_KEY not set. Cannot process voice input.")
        return None, {"model": SARVAM_STT_MODEL, "duration_sec": duration_sec, "bytes": audio_bytes_len, "status": "skipped"}

    while True:
        headers = {
            "api-subscription-key": sarvam_key_rotator.current_key,
        }

        audio_file.seek(0)
        files = {
            "file": ("recording.wav", audio_file.read(), "audio/wav"),
        }
        data = {
            "model": SARVAM_STT_MODEL,
        }

        try:
            response = requests.post(
                SARVAM_STT_TRANSLATE_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=30,
            )
            if response.status_code in (429, 403, 500, 502, 503) and sarvam_key_rotator.rotate():
                st.warning(f"Sarvam key #{sarvam_key_rotator.index} hit an error — rotating to key #{sarvam_key_rotator.index + 1}.")
                continue

            response.raise_for_status()
            result = response.json()
            transcript = result.get("transcript", "")

            stats = {
                "model": SARVAM_STT_MODEL,
                "duration_sec": duration_sec,
                "bytes": audio_bytes_len,
                "status": "success",
            }

            if hasattr(st, "session_state"):
                st.session_state.sarvam_stt_calls = (
                    st.session_state.get("sarvam_stt_calls", 0) + 1
                )
                st.session_state.sarvam_stt_duration_sec = (
                    st.session_state.get("sarvam_stt_duration_sec", 0.0) + duration_sec
                )
                st.session_state.sarvam_stt_bytes = (
                    st.session_state.get("sarvam_stt_bytes", 0) + audio_bytes_len
                )

            return transcript, stats
        except requests.exceptions.RequestException as e:
            if sarvam_key_rotator.rotate():
                st.warning(f"Sarvam STT error ({e}) — rotating to key #{sarvam_key_rotator.index + 1} and retrying.")
                continue
            st.error(f"Sarvam AI speech-to-text-translate failed on all keys. Error: {e}")
            return None, {"model": SARVAM_STT_MODEL, "duration_sec": duration_sec, "bytes": audio_bytes_len, "status": f"failed: {e}"}


# --------------------------------------------------------------------------
# 5. LANGCHAIN + GOOGLE GEMINI INTENT EXTRACTION ENGINE
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# 5. LANGCHAIN + GOOGLE GEMINI INTENT EXTRACTION ENGINE
# --------------------------------------------------------------------------

def build_extraction_chain(api_key: str):
    """
    Build a fresh LangChain structured-output chain bound to a specific
    Gemini API key. include_raw=True ensures we receive the underlying AIMessage
    which contains exact token usage metadata.
    """
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0,
        google_api_key=api_key,
    )
    return llm.with_structured_output(MarineIntentSchema, include_raw=True)


def extract_intent(english_text: str) -> tuple[MarineIntentSchema, dict]:
    """
    Pass an English query (from either the text or voice path) through the
    LangChain extraction chain. Returns (MarineIntentSchema, token_stats_dict).

    On a rate-limit / quota-exhaustion error, rotates to the next available
    Gemini API key (via module-level `key_rotator`) and retries.
    """
    system_instruction = (
        "You are the Access & Understanding module of ORCA, a marine "
        "assistant for Indian fishermen. Extract the structured intent "
        "from the user's query. If a field is not mentioned, set it to null. "
        "intent_type must be one of: find_pfz, weather_alert, safe_route, "
        "geofence_check, general_query."
    )

    while True:
        chain = build_extraction_chain(key_rotator.current_key)
        try:
            result = chain.invoke(
                [
                    ("system", system_instruction),
                    ("human", english_text),
                ]
            )

            parsed = result.get("parsed")
            raw_msg = result.get("raw")

            if parsed is None and result.get("parsing_error"):
                raise result["parsing_error"]

            # Extract token usage metadata from raw AIMessage
            usage = getattr(raw_msg, "usage_metadata", {}) or {}
            prompt_tokens = usage.get("input_tokens", 0)
            completion_tokens = usage.get("output_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            token_stats = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }

            # Update session state token counters
            if hasattr(st, "session_state"):
                st.session_state.total_prompt_tokens = (
                    st.session_state.get("total_prompt_tokens", 0) + prompt_tokens
                )
                st.session_state.total_completion_tokens = (
                    st.session_state.get("total_completion_tokens", 0) + completion_tokens
                )
                st.session_state.total_tokens_used = (
                    st.session_state.get("total_tokens_used", 0) + total_tokens
                )
                st.session_state.llm_call_count = (
                    st.session_state.get("llm_call_count", 0) + 1
                )

            return parsed, token_stats
        except Exception as e:
            if _is_quota_error(e) and key_rotator.rotate():
                st.warning(
                    f"Gemini key #{key_rotator.index + 1} hit a rate limit/quota error — "
                    f"rotating to the next key and retrying."
                )
                continue
            # Not a quota error, or no keys left to rotate to — re-raise
            raise


def run_pipeline(english_text: str) -> tuple[dict, dict]:
    """
    Shared tail-end of the pipeline: English text in, (structured JSON payload, token_stats) out.
    Used by both the text and voice input paths.
    """
    with st.spinner("Extracting structured intent..."):
        try:
            intent_result, token_stats = extract_intent(english_text)
            payload = intent_result.model_dump()
        except Exception as e:
            st.error(f"Intent extraction failed: {e}")
            payload = {
                "intent_type": "general_query",
                "location": None,
                "date": None,
                "vessel_type": None,
                "error": str(e),
            }
            token_stats = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    return payload, token_stats


# --------------------------------------------------------------------------
# 6. STREAMLIT CHAT INTERFACE & SIDEBAR DASHBOARD
# --------------------------------------------------------------------------

# Initialize session state for conversation & token tracking
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": "user"/"assistant", "content": str}

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# --- Gemini token tracking session state ---
if "token_budget" not in st.session_state:
    st.session_state.token_budget = 100000  # Default budget limit: 100k tokens

if "total_prompt_tokens" not in st.session_state:
    st.session_state.total_prompt_tokens = 0

if "total_completion_tokens" not in st.session_state:
    st.session_state.total_completion_tokens = 0

if "total_tokens_used" not in st.session_state:
    st.session_state.total_tokens_used = 0

if "llm_call_count" not in st.session_state:
    st.session_state.llm_call_count = 0

# --- Sarvam AI tracking session state ---
if "sarvam_translate_calls" not in st.session_state:
    st.session_state.sarvam_translate_calls = 0

if "sarvam_translate_chars" not in st.session_state:
    st.session_state.sarvam_translate_chars = 0

if "sarvam_stt_calls" not in st.session_state:
    st.session_state.sarvam_stt_calls = 0

if "sarvam_stt_duration_sec" not in st.session_state:
    st.session_state.sarvam_stt_duration_sec = 0.0

if "sarvam_stt_bytes" not in st.session_state:
    st.session_state.sarvam_stt_bytes = 0


# --- Sidebar: Token & Usage Tracker Dashboard ---
with st.sidebar:
    st.header("📊 Usage & Model Tracker")

    # 1. Active Models & Services Registry
    st.markdown("### 🤖 Active Models & APIs")
    st.markdown(f"- 🧠 **Gemini Intent:** `{GEMINI_MODEL}`")
    st.markdown(f"- 🌐 **Sarvam Translate:** `{SARVAM_TRANSLATE_MODEL}`")
    st.markdown(f"- 🎙️ **Sarvam Voice STT:** `{SARVAM_STT_MODEL}`")
    st.divider()

    # 2. Google Gemini Tokens Remaining
    st.subheader("⚡ Google Gemini Quota")

    used = st.session_state.total_tokens_used
    remaining = max(0, GEMINI_DAILY_TOKEN_QUOTA - used)
    pct_remaining = (remaining / GEMINI_DAILY_TOKEN_QUOTA) * 100.0 if GEMINI_DAILY_TOKEN_QUOTA > 0 else 0.0

    # Prominent Hero Metric showing Tokens Left
    st.metric(
        label="⏳ Tokens Left to Use",
        value=f"{remaining:,}",
        delta=f"-{used:,} used" if used > 0 else "0 used",
        delta_color="inverse",
    )

    st.progress(
        max(0.0, min(1.0, remaining / GEMINI_DAILY_TOKEN_QUOTA)),
        text=f"Quota Left: {pct_remaining:.2f}% ({remaining:,} / {GEMINI_DAILY_TOKEN_QUOTA:,})",
    )

    if remaining == 0:
        st.error("🚨 Daily Gemini Token Quota exhausted!")
    elif pct_remaining <= 20.0:
        st.warning("⚠️ Low quota remaining (<20% left)")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Used Tokens", f"{used:,}")
        st.metric("Prompt Tokens", f"{st.session_state.total_prompt_tokens:,}")
    with col2:
        st.metric("Output Tokens", f"{st.session_state.total_completion_tokens:,}")
        st.metric("API Calls", f"{st.session_state.llm_call_count}")

    st.caption(f"🔑 Active Key: Key #{key_rotator.index + 1} of {len(key_rotator.keys)}")

    st.divider()

    # 3. Sarvam AI Quota Tracker
    st.subheader("🇮🇳 Sarvam AI Quota")

    # Text Translation Quota
    s_chars_used = st.session_state.sarvam_translate_chars
    s_chars_rem = max(0, SARVAM_CHAR_QUOTA - s_chars_used)
    s_chars_pct = (s_chars_rem / SARVAM_CHAR_QUOTA) * 100.0 if SARVAM_CHAR_QUOTA > 0 else 0.0

    st.metric(
        label="⏳ Translation Chars Left",
        value=f"{s_chars_rem:,}",
        delta=f"-{s_chars_used:,} chars used" if s_chars_used > 0 else "0 used",
        delta_color="inverse",
    )
    st.progress(
        max(0.0, min(1.0, s_chars_rem / SARVAM_CHAR_QUOTA)),
        text=f"Translate Quota Left: {s_chars_pct:.1f}% ({s_chars_rem:,} / {SARVAM_CHAR_QUOTA:,})",
    )

    # Voice STT Quota
    s_sec_used = st.session_state.sarvam_stt_duration_sec
    s_sec_rem = max(0.0, SARVAM_AUDIO_QUOTA_SEC - s_sec_used)
    s_sec_pct = (s_sec_rem / SARVAM_AUDIO_QUOTA_SEC) * 100.0 if SARVAM_AUDIO_QUOTA_SEC > 0 else 0.0
    rem_min = round(s_sec_rem / 60.0, 1)
    used_min = round(s_sec_used / 60.0, 1)

    st.metric(
        label="⏳ Voice STT Audio Left",
        value=f"{rem_min} mins ({round(s_sec_rem)}s)",
        delta=f"-{used_min}m used" if s_sec_used > 0 else "0m used",
        delta_color="inverse",
    )
    st.progress(
        max(0.0, min(1.0, s_sec_rem / SARVAM_AUDIO_QUOTA_SEC)),
        text=f"Voice Quota Left: {s_sec_pct:.1f}% ({rem_min}m / {round(SARVAM_AUDIO_QUOTA_SEC/60)}m)",
    )

    sc1, sc2 = st.columns(2)
    with sc1:
        st.metric("Text Calls", f"{st.session_state.sarvam_translate_calls}")
        st.metric("Chars Used", f"{s_chars_used:,}")
    with sc2:
        st.metric("Voice Calls", f"{st.session_state.sarvam_stt_calls}")
        st.metric("Audio Used", f"{s_sec_used:.1f}s ({used_min}m)")

    st.caption(f"🔑 Active Key: Key #{sarvam_key_rotator.index + 1} of {len(sarvam_key_rotator.keys)}")

    st.divider()

    if st.button("🔄 Reset Usage Counters", use_container_width=True):
        st.session_state.total_prompt_tokens = 0
        st.session_state.total_completion_tokens = 0
        st.session_state.total_tokens_used = 0
        st.session_state.llm_call_count = 0
        st.session_state.sarvam_translate_calls = 0
        st.session_state.sarvam_translate_chars = 0
        st.session_state.sarvam_stt_calls = 0
        st.session_state.sarvam_stt_duration_sec = 0.0
        st.session_state.sarvam_stt_bytes = 0
        st.rerun()


st.title("🐋 ORCA — Stage 1: Access & Understanding")
st.caption("Multilingual query intake (text or voice) -> Translation -> Structured Intent Extraction")

# Render existing conversation history on every rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "payload" in message:
            st.json(message["payload"])

        # Sarvam usage tag
        if "sarvam_stats" in message:
            ss = message["sarvam_stats"]
            if ss.get("model") == SARVAM_TRANSLATE_MODEL:
                c_rem = max(0, SARVAM_CHAR_QUOTA - st.session_state.sarvam_translate_chars)
                st.caption(f"⏳ **Chars Left:** {c_rem:,} / {SARVAM_CHAR_QUOTA:,} | 🌐 **Sarvam Translate (`{SARVAM_TRANSLATE_MODEL}`):** {ss.get('chars', 0)} characters")
            elif ss.get("model") == SARVAM_STT_MODEL:
                a_rem_sec = max(0.0, SARVAM_AUDIO_QUOTA_SEC - st.session_state.sarvam_stt_duration_sec)
                a_rem_min = round(a_rem_sec / 60.0, 1)
                st.caption(f"⏳ **Audio Left:** {a_rem_min}m ({round(a_rem_sec)}s) | 🎙️ **Sarvam Voice STT (`{SARVAM_STT_MODEL}`):** {ss.get('duration_sec', 0)}s audio ({round(ss.get('bytes', 0)/1024, 1)} KB)")

        # Gemini token usage tag
        if "token_stats" in message and message["token_stats"].get("total_tokens", 0) > 0:
            ts = message["token_stats"]
            rem = max(0, GEMINI_DAILY_TOKEN_QUOTA - st.session_state.total_tokens_used)
            st.caption(
                f"⏳ **Tokens Left:** {rem:,} / {GEMINI_DAILY_TOKEN_QUOTA:,} | "
                f"⚡ **Google Gemini (`{GEMINI_MODEL}`):** {ts['total_tokens']:,} tokens "
                f"(Prompt: {ts['prompt_tokens']:,} | Output: {ts['completion_tokens']:,})"
            )


def handle_new_query(source_label: str, english_text: str, original_note: str = "", sarvam_stats: dict = None):
    """
    Shared handler that runs the extraction pipeline for a freshly-obtained
    English string (regardless of whether it came from text or voice) and
    appends both the user and assistant turns to session_state.
    """
    if sarvam_stats is None:
        sarvam_stats = {}

    # Record the user's turn
    user_display = original_note if original_note else english_text
    st.session_state.messages.append({"role": "user", "content": user_display})
    with st.chat_message("user"):
        st.markdown(user_display)

    # Run extraction and render the assistant's turn
    with st.chat_message("assistant"):
        st.markdown(f"**Understood ({source_label} -> EN):** {english_text}")
        payload, token_stats = run_pipeline(english_text)
        st.markdown("**Structured Intent Payload (-> Stage 2 Orchestrator):**")
        st.json(payload)

        # Render Sarvam stats tag
        if sarvam_stats.get("model") == SARVAM_TRANSLATE_MODEL:
            c_rem = max(0, SARVAM_CHAR_QUOTA - st.session_state.sarvam_translate_chars)
            st.caption(f"⏳ **Chars Left:** {c_rem:,} / {SARVAM_CHAR_QUOTA:,} | 🌐 **Sarvam Translate (`{SARVAM_TRANSLATE_MODEL}`):** {sarvam_stats.get('chars', 0)} characters")
        elif sarvam_stats.get("model") == SARVAM_STT_MODEL:
            a_rem_sec = max(0.0, SARVAM_AUDIO_QUOTA_SEC - st.session_state.sarvam_stt_duration_sec)
            a_rem_min = round(a_rem_sec / 60.0, 1)
            st.caption(f"⏳ **Audio Left:** {a_rem_min}m ({round(a_rem_sec)}s) | 🎙️ **Sarvam Voice STT (`{SARVAM_STT_MODEL}`):** {sarvam_stats.get('duration_sec', 0)}s audio ({round(sarvam_stats.get('bytes', 0)/1024, 1)} KB)")

        # Render Gemini token usage tag
        if token_stats.get("total_tokens", 0) > 0:
            p_tok = token_stats["prompt_tokens"]
            c_tok = token_stats["completion_tokens"]
            t_tok = token_stats["total_tokens"]
            rem = max(0, GEMINI_DAILY_TOKEN_QUOTA - st.session_state.total_tokens_used)
            st.caption(
                f"⏳ **Tokens Left:** {rem:,} / {GEMINI_DAILY_TOKEN_QUOTA:,} | "
                f"⚡ **Google Gemini (`{GEMINI_MODEL}`):** {t_tok:,} tokens (Prompt: {p_tok:,} | Output: {c_tok:,})"
            )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": f"**Understood ({source_label} -> EN):** {english_text}\n\n"
                       f"**Structured Intent Payload (-> Stage 2 Orchestrator):**",
            "payload": payload,
            "token_stats": token_stats,
            "sarvam_stats": sarvam_stats,
        }
    )


# --- Voice input widget (microphone) ---
st.markdown("**🎙️ Speak in your local language:**")
audio_value = st.audio_input("Click to speak in your local language")

if audio_value is not None:
    audio_id = getattr(audio_value, "file_id", None) or id(audio_value)

    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id

        with st.spinner("Transcribing and translating your voice note..."):
            english_from_audio, sarvam_voice_stats = transcribe_and_translate_audio(audio_value)

        if english_from_audio:
            handle_new_query(
                source_label="Voice",
                english_text=english_from_audio,
                original_note="🎙️ [Voice message]",
                sarvam_stats=sarvam_voice_stats,
            )
        else:
            st.error("Could not process the voice input. Please try again or use the text box below.")

# --- Text chat input box (any Indian language) ---
user_query = st.chat_input("Or type here in your local language...")

if user_query:
    with st.spinner("Translating query..."):
        english_from_text, sarvam_text_stats = translate_to_english(user_query)

    handle_new_query(
        source_label="Text",
        english_text=english_from_text,
        original_note=user_query,
        sarvam_stats=sarvam_text_stats,
    )

