"""
Sagarvani conversation engine.

Deterministic, intent-aware dialogue layer that sits in front of the ORCA
pipeline. It decides *what kind of question* was asked, keeps per-conversation
context (location, last topic, pending questions) and only calls the heavy
10-step pipeline when a real marine-safety decision is requested AND a location
is known.

Safety rules enforced here:
  * never assume a location (no silent "Malpe" default),
  * never invent real-time conditions - if a live feed fails we say so,
  * demo data (DATA_MODE=mock) is always labelled and never yields a go/no-go,
  * static reference data (PFZ registry) is always labelled as such.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Tuple

from agents.conversation_agent import KNOWN_PORTS
from services.session_store import SessionStore
from utils.config import Settings

logger = logging.getLogger("sagarvani.conversation")

SUPPORTED_PLACES = "Malpe, Mangalore, Karwar, Goa, Kochi, Mumbai, Chennai or Visakhapatnam"
OFFICIAL_CHECK = "Please also confirm with the official IMD/INCOIS bulletin or your harbour authority before sailing."

# ─────────────────────────────── data providers ───────────────────────────────


@dataclass
class Conditions:
    ok: bool
    weather: Dict[str, Any] = field(default_factory=dict)
    marine: Dict[str, Any] = field(default_factory=dict)
    weather_error: Optional[str] = None
    marine_error: Optional[str] = None
    fetched_at: str = ""
    mock: bool = False


class ConditionsProvider(Protocol):
    def current(self, lat: float, lon: float) -> Conditions: ...


class LiveConditionsProvider:
    """Open-Meteo weather + marine through the existing weather_processor."""

    def current(self, lat: float, lon: float) -> Conditions:
        from processors.weather_processor import get_combined_forecast

        try:
            fc = get_combined_forecast(lat, lon)
        except Exception as exc:  # network/library failure
            logger.error("Live conditions failed: %s", exc)
            return Conditions(ok=False, weather_error=str(exc), marine_error=str(exc),
                              fetched_at=_now())
        return Conditions(
            ok=True,
            weather=fc.get("weather") or {},
            marine=fc.get("marine") or {},
            weather_error=fc.get("weather_error"),
            marine_error=fc.get("marine_error"),
            fetched_at=fc.get("fetched_at") or _now(),
        )


class MockConditionsProvider:
    """Deterministic demo values for DATA_MODE=mock. Never live, always labelled."""

    def current(self, lat: float, lon: float) -> Conditions:
        return Conditions(
            ok=True,
            weather={
                "temperature_c": 29.0, "wind_speed_kmh": 14.0, "wind_gusts_kmh": 22.0,
                "wind_direction_deg": 250, "precipitation_mm": 0.0,
                "weather_description": "Partly cloudy", "cloud_cover_pct": 40,
            },
            marine={
                "wave_height_m": 1.1, "wave_period_s": 8.0, "swell_wave_height_m": 0.8,
                "sea_state": "Slight", "ocean_current_velocity_ms": 0.3,
            },
            fetched_at="DEMO",
            mock=True,
        )


# ─────────────────────────────── result type ──────────────────────────────────


@dataclass
class EngineResult:
    intent: str
    reply: str
    status: str = "ok"                     # ok | needs_info | degraded
    needs_pipeline: bool = False           # caller should run the ORCA pipeline, then finish_decision()
    location: Optional[Dict[str, Any]] = None
    uses_mock_data: bool = False
    mock_components: List[str] = field(default_factory=list)
    data_sources: List[Dict[str, Any]] = field(default_factory=list)
    follow_ups: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    errors: List[Dict[str, str]] = field(default_factory=list)


# ─────────────────────────────── text helpers ─────────────────────────────────


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _has(q: str, *phrases: str) -> bool:
    return any(re.search(r"\b" + re.escape(p) + r"\b", q) for p in phrases)


_COORD_RE = re.compile(
    r"(-?\d{1,2}(?:\.\d+)?)\s*°?\s*([NnSs])?\s*[,;/ ]\s*(-?\d{1,3}(?:\.\d+)?)\s*°?\s*([EeWw])?"
)
_PLACE_STOP = {
    "me", "my", "the", "a", "an", "sea", "shore", "coast", "here", "there", "this", "that", "it",
    "location", "area", "port", "harbour", "harbor", "boat", "water", "waters", "ocean", "general",
    "today", "tomorrow", "tonight", "morning", "evening", "night", "afternoon", "noon", "time",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "knots", "km",
    "your", "our", "them", "us", "all", "any", "case", "fact", "addition", "short", "general",
}
_PLACE_RE = re.compile(r"\b(?:in|at|near|off|around|for|from)\s+([A-Za-z][A-Za-z\-]+)")


def extract_location(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Return (location, unknown_place). Known ports and explicit coordinates only -
    there is no geocoder, so unknown names are reported back rather than guessed."""
    q = text.lower()
    for port, info in KNOWN_PORTS.items():
        if re.search(r"\b" + re.escape(port) + r"\b", q):
            return {"name": port.capitalize(), "lat": info["lat"], "lon": info["lon"], "source": "port"}, None

    for m in _COORD_RE.finditer(text):
        a, ns, b, ew = m.group(1), m.group(2), m.group(3), m.group(4)
        explicit = bool(ns or ew) or ("." in a and "." in b)
        if not explicit:
            continue
        lat, lon = float(a), float(b)
        if ns and ns.lower() == "s":
            lat = -abs(lat)
        if ew and ew.lower() == "w":
            lon = -abs(lon)
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {"name": f"{lat:.2f}°, {lon:.2f}°", "lat": lat, "lon": lon, "source": "coordinates"}, None

    for m in _PLACE_RE.finditer(text):
        word = m.group(1).lower()
        if word not in _PLACE_STOP and not word.isdigit():
            return None, m.group(1)
    return None, None


# ─────────────────────────────── the engine ───────────────────────────────────

DATA_INTENTS = ("weather", "sea_conditions", "fishing_decision", "fishing_zone", "hazard", "route")


class ConversationEngine:
    def __init__(self, store: SessionStore, settings: Settings,
                 conditions_provider: Optional[ConditionsProvider] = None):
        self.store = store
        self.settings = settings
        if conditions_provider is not None:
            self.conditions = conditions_provider
        elif settings.data_mode == "mock":
            self.conditions = MockConditionsProvider()
        else:
            self.conditions = LiveConditionsProvider()

    # ── session ──────────────────────────────────────────────────────────────
    def _load(self, cid: str) -> Dict[str, Any]:
        return self.store.get(cid) or {
            "conversation_id": cid, "turns": [], "location": None,
            "last_intent": None, "pending_intent": None, "last_summary": None,
        }

    def _save(self, sess: Dict[str, Any], user_text: str, result: EngineResult) -> None:
        sess["turns"] = (sess["turns"] + [
            {"role": "user", "text": user_text},
            {"role": "assistant", "text": result.reply, "intent": result.intent},
        ])[-20:]
        self.store.save(sess["conversation_id"], sess)

    def history(self, cid: str) -> List[Dict[str, Any]]:
        return (self.store.get(cid) or {}).get("turns", [])

    # ── main entry ───────────────────────────────────────────────────────────
    def respond(self, user_text: str, conversation_id: str) -> EngineResult:
        sess = self._load(conversation_id)
        text = (user_text or "").strip()
        result = self._route(text, sess)
        # remember context
        if result.location:
            sess["location"] = result.location
        if result.intent in DATA_INTENTS:
            sess["last_intent"] = result.intent
        if result.status == "needs_info" and result.intent in DATA_INTENTS:
            sess["pending_intent"] = result.intent
        elif result.intent != "clarify_location":
            sess["pending_intent"] = None
        if result.status != "needs_info":
            sess["last_summary"] = result.reply
        self._save(sess, text, result)
        return result

    def _route(self, text: str, sess: Dict[str, Any]) -> EngineResult:
        if not text:
            return EngineResult("empty", "I didn't catch anything. Could you say or type your question again?", "needs_info")

        q = text.lower()
        location, unknown_place = extract_location(text)
        intent = self._classify(q)

        # Pure location reply ("Malpe", "at Karwar", "what about Kochi?")
        if intent is None and (location or unknown_place):
            pending = sess.get("pending_intent") or sess.get("last_intent")
            if pending:
                intent = pending
            elif location:
                return EngineResult(
                    "location_set", f"Got it - {location['name']}. What would you like to know there: weather, wave conditions, or whether it is safe for fishing?",
                    "needs_info", location=location,
                    follow_ups=[f"What is the weather at {location['name']}?", f"Should fishermen go to sea from {location['name']} today?"],
                )

        if intent is None:
            if _has(q, "why", "explain", "how sure", "how confident", "how reliable", "source", "sources"):
                return self._explain(sess)
            return self._fallback(text)

        # Static (location-free) intents
        if intent == "greeting":
            return EngineResult("greeting", "Hello! I am Sagarvani, your marine intelligence assistant. How can I help you today?",
                                follow_ups=["What can you do?", "What is the weather at Malpe?"])
        if intent == "thanks":
            return EngineResult("thanks", "You're welcome! Stay safe at sea. Ask me anything else about marine conditions whenever you like.")
        if intent == "goodbye":
            return EngineResult("goodbye", "Goodbye, and stay safe on the water. I'm here whenever you need marine information.")
        if intent == "capabilities":
            return EngineResult(
                "capabilities",
                "I can help interpret marine conditions, weather information, ocean hazards, fishing-related conditions, and marine safety information. "
                f"Tell me a place ({SUPPORTED_PLACES}) or coordinates and ask, for example, about the weather, wave conditions, or whether it is safe to go fishing.",
                follow_ups=["What is the weather at Mangalore?", "What are the wave conditions near Karwar?", "Should fishermen go to sea today?"],
            )
        if intent == "explain":
            return self._explain(sess)

        # Data intents need a location
        if location is None:
            location = sess.get("location")
        if location is None:
            return self._ask_location(intent, unknown_place)

        return self._answer_with_data(intent, location, q, sess)

    # ── classification ───────────────────────────────────────────────────────
    def _classify(self, q: str) -> Optional[str]:
        greeting = re.match(r"^\s*(hi|hello|hey|namaste|namaskara|vanakkam|good (morning|afternoon|evening))\b", q)
        if _has(q, "thanks", "thank you", "thankyou"):
            return "thanks"
        if _has(q, "bye", "goodbye", "see you"):
            return "goodbye"
        if (_has(q, "what can you do", "what do you do", "who are you", "what are you", "help me", "help", "capabilities", "features")
                and not _has(q, "fishing", "weather")):
            return "capabilities"
        if _has(q, "go to sea", "go fishing", "safe to fish", "safe to go", "safe for fishing", "fishermen", "fisherman",
                "fisher folk", "set sail", "launch the boat", "go out to sea", "sail today", "fishing today", "safe to sail", "go out"):
            return "fishing_decision"
        if _has(q, "pfz", "fishing zone", "fishing zones", "where to fish", "where should i fish", "potential fishing"):
            return "fishing_zone"
        if _has(q, "cyclone", "storm", "tsunami", "warning", "warnings", "alert", "alerts", "hazard", "hazards", "dangerous", "lightning", "squall"):
            return "hazard"
        if _has(q, "wave", "waves", "swell", "sea state", "sea condition", "sea conditions", "tide", "tides", "current", "currents", "rough", "choppy", "ocean condition", "ocean conditions"):
            return "sea_conditions"
        if _has(q, "weather", "rain", "raining", "temperature", "forecast", "wind", "windy", "cloud", "clouds", "hot", "humid", "sunny"):
            return "weather"
        if _has(q, "route", "navigate", "navigation", "course", "path"):
            return "route"
        if _has(q, "why", "explain", "how sure", "how confident", "how reliable", "sources"):
            return "explain"
        if greeting:
            return "greeting"
        return None

    # ── pieces ───────────────────────────────────────────────────────────────
    def _ask_location(self, intent: str, unknown_place: Optional[str]) -> EngineResult:
        if unknown_place:
            reply = (f"I don't have coordinates for \"{unknown_place}\" yet. Please give me a nearby port ({SUPPORTED_PLACES}) "
                     "or latitude and longitude, for example 13.35, 74.70.")
        elif intent == "fishing_decision":
            reply = ("I can help assess conditions, but I need the location and reliable current marine and weather information "
                     f"before providing a meaningful recommendation. Which port or coordinates ({SUPPORTED_PLACES}) are you sailing from?")
        elif intent == "weather":
            reply = f"I can help check the weather for that location. Please provide the location or coordinates (for example {SUPPORTED_PLACES})."
        else:
            reply = f"Which location should I check? Please give me a port ({SUPPORTED_PLACES}) or latitude and longitude."
        return EngineResult(intent, reply, "needs_info", follow_ups=["Malpe", "Mangalore", "13.35, 74.70"])

    def _fallback(self, text: str) -> EngineResult:
        return EngineResult(
            "unknown",
            "I'm not sure I understood that. I can answer questions about weather, wave and sea conditions, ocean hazards, and "
            "whether conditions are suitable for fishing near a given port or coordinates. Could you rephrase, or try one of those?",
            "needs_info",
            follow_ups=["What can you do?", "What is the weather at Malpe?"],
        )

    def _explain(self, sess: Dict[str, Any]) -> EngineResult:
        if not sess.get("last_summary"):
            return EngineResult("explain", "I haven't given you an answer to explain yet. Ask me about the weather, sea conditions or fishing safety first.", "needs_info")
        return EngineResult(
            "explain",
            "Here is how I got my last answer: I used the location you gave me, fetched model forecasts from Open-Meteo for wind, "
            "weather and waves, and applied vessel-specific safety limits. Anything about fishing zones comes from a static reference "
            "list, not live INCOIS data. Forecasts are not observations, so " + OFFICIAL_CHECK[0].lower() + OFFICIAL_CHECK[1:],
        )

    def _answer_with_data(self, intent: str, location: Dict[str, Any], q: str, sess: Dict[str, Any]) -> EngineResult:
        name, lat, lon = location["name"], location["lat"], location["lon"]
        loc_s = f"{name} ({lat:.2f}°N, {lon:.2f}°E)" if location.get("source") == "port" else name

        time_note = ""
        if _has(q, "tomorrow", "tonight", "next week", "day after") or re.search(r"\b\d{1,2}\s*(am|pm)\b", q):
            time_note = " (I can only check current conditions in chat right now, not a specific future time.)"

        # Decision requests are handed to the pipeline (real architecture), except in mock data mode.
        if intent in ("fishing_decision", "fishing_zone", "route") and self.settings.data_mode != "mock":
            return EngineResult(
                intent, "", needs_pipeline=True, location=location,
                data_sources=[], follow_ups=["Why?", "What is the wave height there?"],
            )

        cond = self.conditions.current(lat, lon)
        mock_flag = cond.mock
        mock_label = "DEMO DATA (not live observations): " if mock_flag else ""
        sources = [{
            "name": "Demo dataset" if mock_flag else "Open-Meteo (weather + marine model forecast)",
            "type": "mock" if mock_flag else "live_forecast",
            "fetched_at": cond.fetched_at,
        }]
        mock_components = ["All values are deterministic demo data"] if mock_flag else []

        if intent in ("fishing_decision", "fishing_zone", "route"):  # mock data mode
            w, m = cond.weather, cond.marine
            reply = (f"{mock_label}for {loc_s}, the demo conditions are waves {m.get('wave_height_m')} m and wind {w.get('wind_speed_kmh')} km/h. "
                     "Because this is demo data, I cannot give a go/no-go or fishing-zone recommendation. Switch the backend to live data for a real assessment.")
            return EngineResult(intent, reply, "degraded", location=location, uses_mock_data=True,
                                mock_components=mock_components, data_sources=sources)

        if intent == "hazard":
            parts = ["I can't confirm cyclone, storm or warning status from a verified live alert feed in this chat yet, so please check the IMD bulletin (mausam.imd.gov.in) and INCOIS alerts."]
            extra = self._wind_wave_sentence(cond, loc_s)
            if extra:
                parts.append(extra)
            return EngineResult("hazard", mock_label + " ".join(parts) + time_note, "degraded", location=location,
                                uses_mock_data=mock_flag, mock_components=mock_components, data_sources=sources,
                                follow_ups=["What are the wave conditions there?"])

        if intent == "weather":
            w = cond.weather
            if not cond.ok or cond.weather_error or not w:
                return self._unavailable(intent, location, "weather", cond.weather_error)
            desc = w.get("weather_description") or "conditions unknown"
            bits = [f"{desc}"]
            if w.get("temperature_c") is not None:
                bits.append(f"{w['temperature_c']} °C")
            if w.get("wind_speed_kmh") is not None:
                gust = f" (gusts {w['wind_gusts_kmh']} km/h)" if w.get("wind_gusts_kmh") is not None else ""
                bits.append(f"wind {w['wind_speed_kmh']} km/h{gust}")
            if w.get("precipitation_mm") is not None:
                bits.append(f"rain {w['precipitation_mm']} mm")
            reply = (f"{mock_label}Current weather near {loc_s}: " + ", ".join(bits) + ". "
                     + ("" if mock_flag else f"This is a model forecast from Open-Meteo fetched {cond.fetched_at[:16].replace('T', ' ')}, not a station observation.")
                     + time_note)
            return EngineResult("weather", reply.strip(), location=location, uses_mock_data=mock_flag,
                                mock_components=mock_components, data_sources=sources,
                                follow_ups=["What are the wave conditions there?", "Should fishermen go to sea today?"])

        if intent == "sea_conditions":
            m = cond.marine
            if not cond.ok or cond.marine_error or m.get("wave_height_m") is None:
                return self._unavailable(intent, location, "marine", cond.marine_error)
            bits = [f"wave height {m['wave_height_m']} m"]
            if m.get("wave_period_s") is not None:
                bits.append(f"period {m['wave_period_s']} s")
            if m.get("swell_wave_height_m") is not None:
                bits.append(f"swell {m['swell_wave_height_m']} m")
            if m.get("sea_state"):
                bits.append(f"sea state: {m['sea_state']}")
            if m.get("ocean_current_velocity_ms") is not None:
                bits.append(f"surface current {m['ocean_current_velocity_ms']} m/s")
            reply = (f"{mock_label}Sea conditions near {loc_s}: " + ", ".join(bits) + ". "
                     + ("" if mock_flag else f"Model forecast from Open-Meteo Marine fetched {cond.fetched_at[:16].replace('T', ' ')}. ")
                     + "This is general information, not a go/no-go decision." + time_note)
            return EngineResult("sea_conditions", reply.strip(), location=location, uses_mock_data=mock_flag,
                                mock_components=mock_components, data_sources=sources,
                                follow_ups=["Should fishermen go to sea today?", "What is the weather there?"])

        return self._fallback(q)

    @staticmethod
    def _wind_wave_sentence(cond: Conditions, loc_s: str) -> str:
        bits = []
        if cond.weather.get("wind_speed_kmh") is not None:
            bits.append(f"wind {cond.weather['wind_speed_kmh']} km/h")
        if cond.marine.get("wave_height_m") is not None:
            bits.append(f"waves {cond.marine['wave_height_m']} m")
        return f"For reference, model forecast near {loc_s}: " + ", ".join(bits) + "." if bits else ""

    @staticmethod
    def _unavailable(intent: str, location: Dict[str, Any], kind: str, err: Optional[str]) -> EngineResult:
        logger.warning("Live %s data unavailable for %s: %s", kind, location.get("name"), err)
        return EngineResult(
            intent,
            f"I couldn't retrieve live {kind} data for {location['name']} right now, so I won't guess. Please try again in a moment, "
            "or check the IMD/INCOIS bulletins directly.",
            "degraded", location=location,
            errors=[{"code": f"{kind}_unavailable", "message": (err or "provider returned no data")[:200]}],
            data_sources=[{"name": "Open-Meteo", "type": "live_forecast", "status": "unavailable"}],
        )

    # ── decision wording from the ORCA pipeline ──────────────────────────────
    def finish_decision(self, result: EngineResult, pipeline: Dict[str, Any], vessel_label: str) -> EngineResult:
        """Turn the pipeline's decision package into a spoken-friendly, caveated answer."""
        dec = pipeline.get("decision_package", {}) or {}
        integrity = pipeline.get("data_integrity", {}) or {}
        verdict = dec.get("verdict")
        loc = result.location or {}
        name = loc.get("name", "that location")
        cond = dec.get("conditions", {}) or {}
        wave, wind = cond.get("wave_m"), cond.get("wind_kmh")

        result.data_sources = [
            {"name": "Open-Meteo (weather + marine model forecast)", "type": "live_forecast" if integrity.get("conditions_live") else "unavailable"},
            {"name": "Static reference registry (fishing zones, SST, chlorophyll)", "type": "static_reference"},
            {"name": "Reference geofences (restricted zones)", "type": "static_reference"},
        ]
        result.uses_mock_data = True
        result.mock_components = list(integrity.get("mock_components") or ["Fishing zones and ocean-colour values are static reference data"])
        result.confidence = dec.get("confidence")
        result.follow_ups = ["Why?", "What are the wave conditions there?"]

        if verdict == "REASSESS" and not integrity.get("conditions_live"):
            result.status = "degraded"
            result.reply = (f"I can't assess whether it is safe to go to sea from {name} because live wave and wind data is unavailable right now. "
                            "I won't guess. " + OFFICIAL_CHECK)
            result.errors = [{"code": "live_data_unavailable", "message": "Wave or wind feed unavailable"}]
            return result

        sea = f"wave height about {wave} m and wind about {wind} km/h" if wave is not None and wind is not None else "the current sea state"
        if verdict == "AVOID":
            reasons = "; ".join(v.get("message", "") for v in (pipeline.get("hard_safety_gate", {}).get("fatal_violations") or []))
            result.reply = (f"Not recommended: for a {vessel_label} near {name}, the forecast shows {sea}, which exceeds the safety limits. "
                            f"{reasons} Stay ashore. " + OFFICIAL_CHECK)
        elif verdict == "GO":
            zone = dec.get("best_zone")
            zone_txt = (f" A reference fishing zone in the static registry is {zone}, but that list is not a live INCOIS advisory." if zone and zone != "None" else "")
            result.reply = (f"Based on the current model forecast near {name}, {sea} - within the usual limits for a {vessel_label}, so conditions look workable.{zone_txt} "
                            "Forecasts are not observations and can change. " + OFFICIAL_CHECK)
        else:  # REASSESS with live data
            result.reply = (f"Sea conditions near {name} ({sea}) are within limits for a {vessel_label}, but I found no suitable reference fishing zone in range. " + OFFICIAL_CHECK)
        return result
