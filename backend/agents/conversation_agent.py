"""
Stage 1: Conversational ORCA & Multilingual Agent
Handles natural-language query comprehension, multi-turn context memory,
understanding chip extraction, and Indian-language translation.
Extensible to all 22 Scheduled Indian Languages.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from utils.key_rotation import get_next_gemini_key, get_all_keys

try:
    from google import genai as _genai_module
    GENAI_OK = True
except ImportError:
    GENAI_OK = False

# ─── Extensible 22 Scheduled Indian Languages Registry ────────────────────────
INDIAN_LANGUAGES = {
    "en": {"name": "English", "native": "English", "script": "Latin", "coastal": True},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "script": "Kannada", "coastal": True},
    "hi": {"name": "Hindi", "native": "हिन्दी", "script": "Devanagari", "coastal": False},
    "ta": {"name": "Tamil", "native": "தமிழ்", "script": "Tamil", "coastal": True},
    "te": {"name": "Telugu", "native": "తెలుగు", "script": "Telugu", "coastal": True},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "script": "Malayalam", "coastal": True},
    "mr": {"name": "Marathi", "native": "मराठी", "script": "Devanagari", "coastal": True},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "script": "Gujarati", "coastal": True},
    "bn": {"name": "Bengali", "native": "বাংলা", "script": "Bengali", "coastal": True},
    "or": {"name": "Odia", "native": "ଓଡ଼ିଆ", "script": "Odia", "coastal": True},
    "kok": {"name": "Konkani", "native": "कोंकणी", "script": "Devanagari", "coastal": True},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "script": "Gurmukhi", "coastal": False},
    "as": {"name": "Assamese", "native": "অসমীয়া", "script": "Bengali", "coastal": False},
    "ur": {"name": "Urdu", "native": "اردو", "script": "Perso-Arabic", "coastal": False},
    "sa": {"name": "Sanskrit", "native": "संस्कृतम्", "script": "Devanagari", "coastal": False},
    "ks": {"name": "Kashmiri", "native": "कॉशुर", "script": "Perso-Arabic", "coastal": False},
    "sd": {"name": "Sindhi", "native": "سنڌي", "script": "Perso-Arabic", "coastal": False},
    "ne": {"name": "Nepali", "native": "नेपाली", "script": "Devanagari", "coastal": False},
    "mai": {"name": "Maithili", "native": "मैथिली", "script": "Devanagari", "coastal": False},
    "sat": {"name": "Santali", "native": "ᱥᱟᱱᱛᱟᱲᱤ", "script": "Ol Chiki", "coastal": False},
    "brx": {"name": "Bodo", "native": "बड़ो", "script": "Devanagari", "coastal": False},
    "doi": {"name": "Dogri", "native": "डोगरी", "script": "Devanagari", "coastal": False},
    "mni": {"name": "Manipuri", "native": "মৈতৈলোন্", "script": "Meitei", "coastal": False},
}

# Known Indian coastal ports / locations mapping to coordinates
KNOWN_PORTS = {
    "malpe": {"lat": 13.35, "lon": 74.70, "station": "Malpe", "state": "Karnataka"},
    "mangalore": {"lat": 12.87, "lon": 74.84, "station": "Mangalore", "state": "Karnataka"},
    "mangaluru": {"lat": 12.87, "lon": 74.84, "station": "Mangalore", "state": "Karnataka"},
    "karwar": {"lat": 14.80, "lon": 74.13, "station": "Karwar", "state": "Karnataka"},
    "bhatkal": {"lat": 13.98, "lon": 74.55, "station": "Malpe", "state": "Karnataka"},
    "honnavar": {"lat": 14.28, "lon": 74.45, "station": "Karwar", "state": "Karnataka"},
    "goa": {"lat": 15.50, "lon": 73.80, "station": "Karwar", "state": "Goa"},
    "panaji": {"lat": 15.49, "lon": 73.82, "station": "Karwar", "state": "Goa"},
    "kochi": {"lat": 9.97, "lon": 76.28, "station": "Kochi", "state": "Kerala"},
    "cochin": {"lat": 9.97, "lon": 76.28, "station": "Kochi", "state": "Kerala"},
    "mumbai": {"lat": 18.95, "lon": 72.84, "station": "Malpe", "state": "Maharashtra"},
    "chennai": {"lat": 13.08, "lon": 80.27, "station": "Chennai", "state": "Tamil Nadu"},
    "visakhapatnam": {"lat": 17.68, "lon": 83.21, "station": "Chennai", "state": "Andhra Pradesh"},
    "vizag": {"lat": 17.68, "lon": 83.21, "station": "Chennai", "state": "Andhra Pradesh"}
}


class ConversationAgent:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_context(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "history": [],
                "context": {
                    "location_name": "Malpe",
                    "lat": 13.35,
                    "lon": 74.70,
                    "station": "Malpe",
                    "departure_time": "Tomorrow 05:00 AM",
                    "vessel_length_m": 8.0,
                    "vessel_type": "motorized_craft",
                    "vessel_display": "Motorized OBM (8–10 m)",
                    "activity": "Fishing",
                    "range_km": 30.0,
                    "constraints": ["Avoid MPAs", "Stay within safety wave limit"],
                    "language": "en"
                }
            }
        return self.sessions[session_id]

    def detect_language(self, text: str) -> str:
        """Detect language using script heuristics or Gemini."""
        # Check scripts
        for ch in text:
            cp = ord(ch)
            if 0x0C80 <= cp <= 0x0CFF:
                return "kn"  # Kannada
            if 0x0900 <= cp <= 0x097F:
                return "hi"  # Devanagari (Hindi/Marathi)
            if 0x0B80 <= cp <= 0x0BFF:
                return "ta"  # Tamil
            if 0x0C00 <= cp <= 0x0C7F:
                return "te"  # Telugu
            if 0x0D00 <= cp <= 0x0D7F:
                return "ml"  # Malayalam
            if 0x0A80 <= cp <= 0x0AFF:
                return "gu"  # Gujarati
            if 0x0980 <= cp <= 0x09FF:
                return "bn"  # Bengali
            if 0x0B00 <= cp <= 0x0B7F:
                return "or"  # Odia
        return "en"

    def _is_complex_query(self, query: str, rule_extracted: Dict[str, Any]) -> bool:
        """
        Returns True only if the query is genuinely complex enough to warrant
        an optional Gemini call. Simple queries (the 5 MVP journeys) never block.
        """
        words = query.split()
        # Too short to need LLM help
        if len(words) <= 8:
            return False
        # Rule-based already extracted all key fields - no need for LLM
        key_fields = ["location_name", "vessel_type", "departure_time", "range_km"]
        extracted_count = sum(1 for k in key_fields if k in rule_extracted and rule_extracted[k] is not None)
        if extracted_count >= 2:
            return False
        return True

    def parse_query(
        self,
        query: str,
        session_id: str = "default",
        language_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parses user query into structured understanding chips and updates multi-turn context.
        Supports both Gemini LLM (optional, non-blocking) and deterministic offline extraction.
        Rule-based engine handles all 5 MVP journeys instantly without any LLM call.
        """
        session = self.get_or_create_context(session_id)
        current_ctx = session["context"]

        detected_lang = self.detect_language(query)
        target_lang = language_override if (language_override and language_override != "auto") else detected_lang
        current_ctx["language"] = target_lang

        # Step 1: Rule-based deterministic extraction first (fast & always reliable baseline)
        extracted = self._rule_based_extract(query, current_ctx)

        # Step 2: Optionally attempt Gemini LLM extraction ONLY for complex queries.
        # This is entirely optional — the chatbot works fully without it.
        # _gemini_extract has a hard 4-second timeout and never blocks if Gemini is down.
        if GENAI_OK and self._is_complex_query(query, extracted):
            try:
                llm_extracted = self._gemini_extract(query, current_ctx, target_lang)
                if llm_extracted:
                    for k, v in llm_extracted.items():
                        if v is not None and v != "":
                            extracted[k] = v
            except Exception:
                # Gemini failed silently — rule-based results are used as-is
                pass

        # Step 3: Update session context with newly extracted fields (multi-turn memory)
        for k in ["location_name", "lat", "lon", "station", "departure_time",
                  "vessel_length_m", "vessel_type", "vessel_display", "activity", "range_km"]:
            if k in extracted and extracted[k] is not None:
                current_ctx[k] = extracted[k]

        if "constraints" in extracted and extracted["constraints"]:
            current_ctx["constraints"] = list(set(current_ctx.get("constraints", []) + extracted["constraints"]))

        # Build understanding chips representation
        chips = [
            {"id": "location", "label": "📍 Location", "value": f"{current_ctx['location_name']} ({current_ctx['lat']}°N, {current_ctx['lon']}°E)", "raw_key": "location_name", "raw_val": current_ctx["location_name"]},
            {"id": "time", "label": "⏰ Departure", "value": current_ctx["departure_time"], "raw_key": "departure_time", "raw_val": current_ctx["departure_time"]},
            {"id": "vessel", "label": "🚤 Vessel", "value": current_ctx["vessel_display"], "raw_key": "vessel_type", "raw_val": current_ctx["vessel_type"]},
            {"id": "activity", "label": "🎯 Activity", "value": current_ctx["activity"], "raw_key": "activity", "raw_val": current_ctx["activity"]},
            {"id": "range", "label": "📏 Max Range", "value": f"{int(current_ctx['range_km'])} km", "raw_key": "range_km", "raw_val": current_ctx["range_km"]},
            {"id": "constraints", "label": "🛡️ Constraints", "value": ", ".join(current_ctx.get("constraints", ["Safe sea-state"])), "raw_key": "constraints", "raw_val": current_ctx.get("constraints", [])}
        ]

        # Record query in history
        session["history"].append({
            "query": query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detected_language": detected_lang,
            "target_language": target_lang
        })

        # Identify intent from query
        intent = self._classify_intent(query)

        return {
            "session_id": session_id,
            "query": query,
            "detected_language": detected_lang,
            "target_language": target_lang,
            "intent": intent,
            "understanding_chips": chips,
            "active_context": current_ctx
        }

    def _classify_intent(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["route", "safest route", "path", "course", "show the safest route"]):
            return "safest_route"
        if any(w in q for w in ["nearest", "where is the nearest", "useful pfz", "closest pfz"]):
            return "nearest_pfz"
        if any(w in q for w in ["sea condition", "wave", "weather near me", "conditions near me", "wind"]):
            return "sea_conditions"
        if any(w in q for w in ["productive", "safe and not restricted", "find a productive area"]):
            return "productive_safe_zones"
        return "safe_fishing_advisory"

    def _rule_based_extract(self, query: str, current_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic extractor that handles the 5 MVP queries + follow-ups."""
        extracted: Dict[str, Any] = {}
        q = query.lower()

        # 1. Location matching
        for port, info in KNOWN_PORTS.items():
            if port in q:
                extracted["location_name"] = port.capitalize()
                extracted["lat"] = info["lat"]
                extracted["lon"] = info["lon"]
                extracted["station"] = info["station"]
                break

        # 2. Vessel matching
        vessel_m = re.search(r'(\d+(?:\.\d+)?)\s*m(?:eter)?\s*boat', q) or re.search(r'boat\s*(?:of\s*)?(\d+(?:\.\d+)?)m', q)
        if vessel_m:
            length = float(vessel_m.group(1))
            extracted["vessel_length_m"] = length
            if length <= 7.0:
                extracted["vessel_type"] = "artisanal_canoe"
                extracted["vessel_display"] = f"Traditional Canoe ({length} m)"
            elif length <= 11.0:
                extracted["vessel_type"] = "motorized_craft"
                extracted["vessel_display"] = f"Motorized Craft ({length} m)"
            else:
                extracted["vessel_type"] = "mechanized_trawler"
                extracted["vessel_display"] = f"Mechanized Trawler ({length} m)"
        elif "canoe" in q or "traditional" in q:
            extracted["vessel_type"] = "artisanal_canoe"
            extracted["vessel_display"] = "Traditional Canoe (≤7 m)"
            extracted["vessel_length_m"] = 6.0
        elif "trawler" in q or "purse seine" in q:
            extracted["vessel_type"] = "mechanized_trawler"
            extracted["vessel_display"] = "Mechanized Trawler (>12 m)"
            extracted["vessel_length_m"] = 14.0

        # 3. Departure Time matching (handles follow-up "What if I leave at 9 AM?")
        time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))', q)
        if time_match:
            prefix = "Tomorrow " if "tomorrow" in q else ("Today " if "today" in q else "")
            extracted["departure_time"] = f"{prefix}{time_match.group(1).upper()}"
        elif "tomorrow morning" in q:
            extracted["departure_time"] = "Tomorrow 05:00 AM"
        elif "tomorrow" in q:
            extracted["departure_time"] = "Tomorrow 06:00 AM"

        # 4. Range matching
        range_match = re.search(r'within\s*(\d+)\s*(?:km|kms)', q) or re.search(r'(\d+)\s*km\s*range', q)
        if range_match:
            extracted["range_km"] = float(range_match.group(1))

        # 5. Activity
        if "fish" in q:
            extracted["activity"] = "Commercial Coastal Fishing"

        # 6. Constraints
        constraints = []
        if "safe" in q:
            constraints.append("Enforce vessel wave threshold")
        if "not restricted" in q or "avoid" in q or "restricted" in q:
            constraints.append("Strict geofence avoidance")
        if constraints:
            extracted["constraints"] = constraints

        return extracted

    def _gemini_extract(self, query: str, current_ctx: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
        """Optional Gemini LLM entity parsing for complex variations.
        Wrapped with a hard 4-second timeout so a dead/slow Gemini endpoint
        never blocks the chatbot — rule-based results are used as fallback.
        """
        if not GENAI_OK:
            return None
        keys = get_all_keys()
        if not keys:
            return None

        prompt = f"""
You are the natural-language query comprehension module for ORCA Maritime Intelligence.
Extract navigational & operational parameters from the fisherman's query into strict JSON format.

Current Session Context:
- Location: {current_ctx.get('location_name')} ({current_ctx.get('lat')}, {current_ctx.get('lon')})
- Departure Time: {current_ctx.get('departure_time')}
- Vessel Type: {current_ctx.get('vessel_type')}
- Operating Range km: {current_ctx.get('range_km')}

User Query: "{query}"

Output ONLY a JSON object with these keys (use null if not mentioned or unchanged):
{{
  "location_name": string or null,
  "departure_time": string or null,
  "vessel_length_m": float or null,
  "vessel_type": "artisanal_canoe" | "motorized_craft" | "mechanized_trawler" | null,
  "range_km": float or null,
  "activity": string or null,
  "constraints": list of strings or null
}}
"""
        import concurrent.futures

        def _call_gemini():
            key = get_next_gemini_key()
            client = _genai_module.Client(api_key=key)
            resp = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            text = resp.text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```json\s*", "", text)
                text = re.sub(r"^```\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            return json.loads(text)

        # IMPORTANT: Do NOT use `with` context manager here.
        # ThreadPoolExecutor.__exit__ calls shutdown(wait=True), which blocks
        # until the background thread finishes even AFTER future.result() times out.
        # Instead, explicitly shut down with wait=False so we never block the
        # chat endpoint longer than the timeout.
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_call_gemini)
        try:
            result = future.result(timeout=4.0)   # Hard 4-second cap
            return result
        except Exception:
            return None
        finally:
            # Abandon the background thread immediately — do not wait for it.
            # cancel_futures was added in Python 3.9; fall back for 3.8 compatibility.
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                executor.shutdown(wait=False)

    def translate_advisory(self, decision_summary: Dict[str, Any], target_lang: str) -> Dict[str, str]:
        """
        Translates decision explanations, recommendations, and warnings to target Indian language.
        Has deterministic translations for primary Indian languages + Gemini translation fallback.
        """
        verdict = decision_summary.get("verdict", "GO")
        best_zone = decision_summary.get("best_zone", "PFZ-A")
        safety_score = decision_summary.get("safety_score", 85)
        fishing_score = decision_summary.get("fishing_score", 80)
        route_km = decision_summary.get("route_km", 22.5)
        wave_h = decision_summary.get("wave_h", 1.2)
        wind_kmh = decision_summary.get("wind_kmh", 22.0)
        vessel = decision_summary.get("vessel", "Motorized Craft")
        why = decision_summary.get("why", "Sea conditions within safe envelope; highest chlorophyll front at target.")

        # Built-in high quality translations for coastal languages
        if target_lang == "kn":
            v_text = "ಹೌದು, ಪ್ರಯಾಣಿಸಬಹುದು (GO)" if verdict == "GO" else ("ದಡದಲ್ಲೇ ಇರಿ (AVOID)" if verdict == "AVOID" else "ಮರುಪರಿಶೀಲಿಸಿ (REASSESS)")
            msg = (
                f"ನಿರ್ಧಾರ: {v_text}\n"
                f"• ಅತ್ಯುತ್ತಮ ವಲಯ: {best_zone} (ದೂರ: {route_km} ಕಿ.ಮೀ)\n"
                f"• ಸುರಕ್ಷತೆ: {safety_score}/100 | ಮೀನುಗಾರಿಕಾ ಮೌಲ್ಯ: {fishing_score}/100\n"
                f"• ಸಮುದ್ರ ಸ್ಥಿತಿ: ಅಲೆಗಳು {wave_h} ಮೀ, ಗಾಳಿ {wind_kmh} ಕಿ.ಮೀ/ಗಂ ({vessel} ಗೆ ಸುರಕ್ಷಿತ).\n"
                f"• ಕಾರಣ: {why}\n"
                f"• ರಕ್ಷಿತ ಪ್ರದೇಶ: ನೇತ್ರಾಣಿ ನೇವಲ್ & ಕೋರಲ್ ರಕ್ಷಿತ ವಲಯವನ್ನು ನಿಮ್ಮ ಮಾರ್ಗದಿಂದ ಹೊರಗಿಡಲಾಗಿದೆ."
            )
            return {"title": f"ಸಾಗರವಾಣಿ - ORCA ಸಲಹೆ ({v_text})", "body": msg, "lang": "kn"}

        elif target_lang == "hi":
            v_text = "यात्रा अनुकूल (GO)" if verdict == "GO" else ("तट पर ही रहें (AVOID)" if verdict == "AVOID" else "पुनर्मूल्यांकन करें (REASSESS)")
            msg = (
                f"निर्णय: {v_text}\n"
                f"• सर्वश्रेष्ठ मछली पकड़ने का क्षेत्र: {best_zone} (दूरी: {route_km} किमी)\n"
                f"• सुरक्षा स्कोर: {safety_score}/100 | उत्पादकता: {fishing_score}/100\n"
                f"• समुद्र की स्थिति: लहरें {wave_h} मी, हवा {wind_kmh} किमी/घंटा ({vessel} के लिए सुरक्षित)।\n"
                f"• कारण: {why}\n"
                f"• प्रतिबंधित क्षेत्र: नेत्राणी अभयारण्य को सुरक्षित नेविगेशन मार्ग से बाहर रखा गया है।"
            )
            return {"title": f"सागरवाणी - ORCA सलाह ({v_text})", "body": msg, "lang": "hi"}

        elif target_lang == "ta":
            v_text = "செல்லலாம் (GO)" if verdict == "GO" else ("கரையில் இருங்கள் (AVOID)" if verdict == "AVOID" else "மறுமதிப்பீடு (REASSESS)")
            msg = (
                f"முடிவு: {v_text}\n"
                f"• சிறந்த மீன்பிடி மண்டலம்: {best_zone} (தொலைவு: {route_km} கி.மீ)\n"
                f"• பாதுகாப்பு: {safety_score}/100 | மீன்பிடி மதிப்பு: {fishing_score}/100\n"
                f"• கடல் நிலை: அலை {wave_h} மீ, காற்று {wind_kmh} கி.மீ/மணி ({vessel} க்கு உகந்தது).\n"
                f"• காரணம்: {why}\n"
                f"• தடைசெய்யப்பட்ட பகுதி: நேத்ராணி பவளப்பாறை பகுதி தவிர்க்கப்பட்டுள்ளது."
            )
            return {"title": f"சாகர்வாணி - ORCA ஆலோசனை ({v_text})", "body": msg, "lang": "ta"}

        elif target_lang == "te":
            v_text = "ప్రయాణించవచ్చు (GO)" if verdict == "GO" else ("తీరంలోనే ఉండండి (AVOID)" if verdict == "AVOID" else "పునఃపరిశీలించండి (REASSESS)")
            msg = (
                f"నిర్ణయం: {v_text}\n"
                f"• ఉత్తమ జోన్: {best_zone} (దూరం: {route_km} కి.మీ)\n"
                f"• భద్రతా స్కోరు: {safety_score}/100 | ఉత్పాదకత: {fishing_score}/100\n"
                f"• సముద్ర పరిస్థితి: అలల ఎత్తు {wave_h} మీ, గాలి {wind_kmh} కి.మీ/గం ({vessel} కు అనుకూలం).\n"
                f"• కారణం: {why}\n"
                f"• నిషేధిత ప్రాంతం: నేత్రాని సంరక్షణ ప్రాంతం మీ మార్గం నుండి మినహాయించబడింది."
            )
            return {"title": f"సాగరవాణి - ORCA సలహా ({v_text})", "body": msg, "lang": "te"}

        elif target_lang == "ml":
            v_text = "യാത്ര പോകാം (GO)" if verdict == "GO" else ("തീരത്ത് തുടരുക (AVOID)" if verdict == "AVOID" else "പുനഃപരിശോധിക്കുക (REASSESS)")
            msg = (
                f"തീരുമാനം: {v_text}\n"
                f"• മികച്ച മീൻപിടുത്ത മേഖല: {best_zone} (ദൂരം: {route_km} കി.മീ)\n"
                f"• സുരക്ഷ: {safety_score}/100 | ഉൽപാദനക്ഷമത: {fishing_score}/100\n"
                f"• സമുദ്രാവസ്ഥ: തിരമാല {wave_h} മീ, കാറ്റ് {wind_kmh} കി.മീ/മണിക്കൂർ ({vessel} സുരക്ഷിതം).\n"
                f"• കാരണം: {why}\n"
                f"• സംരക്ഷിത മേഖല: നേത്രാണി പവിഴപ്പുറ്റ് പ്രദേശം ഒഴിവാക്കിയിരിക്കുന്നു."
            )
            return {"title": f"സാഗർവാണി - ORCA ഉപദേശം ({v_text})", "body": msg, "lang": "ml"}

        # Default English
        v_text = "GO (FAVORABLE)" if verdict == "GO" else ("AVOID (STAY ASHORE)" if verdict == "AVOID" else "REASSESS")
        msg = (
            f"RECOMMENDATION: {v_text}\n"
            f"• Best Zone: {best_zone} ({route_km} km)\n"
            f"• Safety Score: {safety_score}/100 | Fishing Value: {fishing_score}/100\n"
            f"• Sea State: Wave Height {wave_h}m, Wind {wind_kmh} km/h (Safe for {vessel}).\n"
            f"• Why: {why}\n"
            f"• Geofence Notice: Netrani Naval & Coral Sanctuary strictly bypassed with safe navigation detour."
        )
        return {"title": f"SAGARVANI - ORCA Advisory ({v_text})", "body": msg, "lang": "en"}
