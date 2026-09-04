/**
 * SAGARVANI — ORCA Marine Intelligence & Decision Support System
 * Core Controller: Tide Station ↔ Map Synchronization & Global Centralized Multilingual UI
 * SIH 2026 | Problem Statement: SIH26176
 */

const API = 'http://localhost:8000';
let activeSessionId = 'orca_session_' + Date.now();
let leafletMap = null;
let currentLanguage = 'en';

// ─── SINGLE SOURCE OF TRUTH: TIDE STATIONS REGISTRY ─────────────────────────────
const TIDE_STATIONS_REGISTRY = {
  "Malpe": {
    name: "Malpe",
    label: "Malpe Harbor (Karnataka)",
    lat: 13.35,
    lon: 74.70,
    state: "Karnataka",
    description: "Malpe Commercial Fishing Harbor & Beach"
  },
  "Mangalore": {
    name: "Mangalore",
    label: "Mangalore Port (Karnataka)",
    lat: 12.87,
    lon: 74.84,
    state: "Karnataka",
    description: "Old Mangalore Port / Panambur Ocean State Station"
  },
  "Karwar": {
    name: "Karwar",
    label: "Karwar Bay (Karnataka)",
    lat: 14.81,
    lon: 74.13,
    state: "Karnataka",
    description: "Karwar Baithkol Harbor & Outer Bay"
  },
  "Kochi": {
    name: "Kochi",
    label: "Kochi Harbor (Kerala)",
    lat: 9.94,
    lon: 76.26,
    state: "Kerala",
    description: "Cochin Fisheries Harbor & Mattancherry Channel"
  },
  "Chennai": {
    name: "Chennai",
    label: "Chennai Port (Tamil Nadu)",
    lat: 13.08,
    lon: 80.29,
    state: "Tamil Nadu",
    description: "Chennai Port & Kasimedu / Royapuram Harbor"
  }
};

let mapLayers = {
  boat: null,
  pfzMarkers: [],
  recTarget: null,
  recCircle: null,
  safeRoute: null,
  blockedRoute: null,
  hazardCircles: [],
  hazardMarkers: []
};

// ─── CENTRALIZED EXTENSIBLE I18N SYSTEM ─────────────────────────────────────────
const I18N_TRANSLATIONS = {
  en: {
    badge_agentic: "AGENTIC AI",
    topbar_subtitle: "ORCA — Ocean Risk & Coastal Advisory System · SIH 2026 (Problem: SIH26176)",
    backend_live: "⬤ Backend Live",
    backend_offline: "⬤ Backend Offline",
    chat_placeholder: "Ask ORCA: e.g. 'I have a 5 m boat. Can I leave Malpe at 5 AM tomorrow and fish within 30 km?'",
    btn_analyze_query: "Analyze Query",
    chat_agent_title: "ORCA Agentic Synthesis",
    demo_journeys_label: "⚡ 5 MVP Demo Journeys:",
    journey_1: "1. Can I safely go fishing tomorrow morning?",
    journey_2: "2. Where is the nearest useful PFZ?",
    journey_3: "3. What are the sea conditions near me?",
    journey_4: "4. Find productive area safe & not restricted",
    journey_5: "5. Show safest route to selected area",
    chips_header: "🧠 Extracted Operational Understanding (Click any chip to edit):",
    chips_reset: "Reset Scenario",
    chip_location: "Location",
    chip_departure: "Departure",
    chip_vessel: "Vessel",
    chip_activity: "Activity",
    chip_range: "Range",
    chip_constraints: "Constraints",
    card_scenario_controls: "🎯 Scenario Controls & Query",
    lbl_tide_station: "Tide Station",
    lbl_latitude: "Latitude (°N)",
    lbl_longitude: "Longitude (°E)",
    lbl_vessel_class: "Vessel Class",
    lbl_dep_window: "Departure Window",
    lbl_max_range: "Max Range (km)",
    opt_vessel_canoe: "Traditional Canoe (≤7 m)",
    opt_vessel_motorized: "Motorized OBM (8–10 m)",
    opt_vessel_trawler: "Mechanized Trawler (>12 m)",
    opt_time_tomorrow_05am: "Tomorrow 05:00 AM (Early Ebb)",
    opt_time_tomorrow_09am: "Tomorrow 09:00 AM (High Tide)",
    opt_time_tomorrow_02pm: "Tomorrow 02:00 PM (Afternoon)",
    opt_time_today_now: "Today Immediate Departure",
    btn_run_decision_loop: "Run Full Decision Loop",
    card_orca_pipeline: "⚙️ ORCA 10-Step Pipeline Engine",
    pipe_0: "Query Received",
    pipe_1: "Intent Interpreted",
    pipe_2: "Plan Generated",
    pipe_3: "Data Retrieved",
    pipe_4: "Normalised",
    pipe_5: "Reasoning",
    pipe_6: "Safety Constrained",
    pipe_7: "Ranked",
    pipe_8: "Verified",
    pipe_9: "Advisory Delivered",
    card_maritime_limits: "🗺️ Maritime Limits & Baseline",
    card_exec_rec: "🎯 Executive Recommendation",
    status_standby: "STANDBY",
    status_approved: "APPROVED",
    status_rejected: "REJECTED",
    status_reassess: "REASSESS",
    verdict_go: "GO (FAVORABLE)",
    verdict_avoid: "AVOID (STAY ASHORE)",
    verdict_reassess: "REASSESS (NO SAFE PFZ)",
    verdict_sub_go: "Safe Sea-State · Deterministic Safety Gate Passed",
    verdict_sub_avoid: "Exceeds Vessel Limits or Critical Hazard Active",
    verdict_sub_reassess: "Review Alternative Departure or Operating Window",
    dec_best_zone: "Best Fishing Zone",
    dec_dep_window: "Best Departure Window",
    dec_safety_score: "Safety Score",
    dec_fishing_value: "Fishing Value",
    dec_safest_route: "Safest Route",
    dec_confidence: "Data Confidence",
    dec_why_label: "🔍 Why this decision? (Evidence-Backed Explanation)",
    card_map_title: "🗺️ Interactive Operational Map & Safest Route",
    btn_map_center: "⌖ Center",
    btn_map_route: "Route",
    btn_map_hazards: "Hazards",
    leg_boat: "Departure Boat",
    leg_pfz: "Candidate PFZ",
    leg_rec: "Recommended PFZ",
    leg_danger: "Restricted MPA (Avoid)",
    leg_safe_route: "Safest Route",
    leg_avoided: "Avoided Hazard",
    metric_pfz: "PFZ Status",
    metric_sst: "Sea Surface Temp",
    metric_chla: "Chlorophyll-a",
    metric_wave: "Wave Height (Hs)",
    metric_tide: "Tidal State",
    metric_safety_gate: "Safety Gate",
    card_sva_title: "🚢 Small Vessel Advisory (SVA) — Hard Limits",
    card_sat_title: "🛰️ Satellite Products — EOS-06 / Oceansat-3",
    card_tide_title: "🌊 Tidal Forecast — INCOIS Harmonic Model",
    card_weather_title: "⛈️ Weather · Lightning · Cyclone Warnings",
    card_advisory_title: "🤖 Multilingual Advisory — ORCA Agentic Synthesis",
    advisory_placeholder: "Run Full Analysis or ask a question in Indian languages to generate bilingual decision recommendations.",
    card_erddap_title: "📦 ERDDAP Machine-Readable Dataset",
    card_evidence_title: "🔍 Evidence Trail & Data Provenance Audit",
    sva_clear_to_sail: "✅ CLEAR TO SAIL",
    sva_do_not_sail: "🚫 DO NOT SAIL",
    sva_max_wave: "Max Wave Height",
    sva_max_wind: "Max Wind Speed",
    sva_max_dist: "Max Distance",
    sva_max_beaufort: "Max Beaufort",
    sat_fish_prod: "Productivity",
    cyclone_no_active: "✓ No active cyclone in coastal marine sector",
    lightning_risk: "Lightning Risk"
  },
  kn: {
    badge_agentic: "ಏಜೆಂಟಿಕ್ AI",
    topbar_subtitle: "ORCA — ಸಮುದ್ರ ಅಪಾಯ & ಕರಾವಳಿ ಎಚ್ಚರಿಕೆ ವ್ಯವಸ್ಥೆ · SIH 2026",
    backend_live: "⬤ ಸರ್ವರ್ ಲೈವ್ ಆಗಿದೆ",
    backend_offline: "⬤ ಸರ್ವರ್ ಆಫ್‌ಲೈನ್ ಆಗಿದೆ",
    chat_placeholder: "ORCA ಅನ್ನು ಕೇಳಿ: ಉದಾ: 'ನನ್ನ ಬಳಿ 5 ಮೀಟರ್ ದೋಣಿ ಇದೆ. ನಾಳೆ ಬೆಳಿಗ್ಗೆ 5 ಗಂಟೆಗೆ ಮಾಲ್ಪೆಯಿಂದ 30 ಕಿ.ಮೀ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ಮೀನುಗಾರಿಕೆಗೆ ಹೋಗಬಹುದೇ?'",
    btn_analyze_query: "ಪ್ರಶ್ನೆ ವಿಶ್ಲೇಷಿಸಿ",
    demo_journeys_label: "⚡ 5 ಪ್ರಮುಖ ಡೆಮೊ ಪಯಣಗಳು:",
    journey_1: "1. ನಾಳೆ ಬೆಳಿಗ್ಗೆ ನಾನು ಸುರಕ್ಷಿತವಾಗಿ ಮೀನುಗಾರಿಕೆಗೆ ಹೋಗಬಹುದೇ?",
    journey_2: "2. ಸಮೀಪದ ಉಪಯುಕ್ತ PFZ ಎಲ್ಲಿದೆ?",
    journey_3: "3. ನನ್ನ ಸಮೀಪದ ಸಮುದ್ರ ಪರಿಸ್ಥಿತಿ ಹೇಗಿದೆ?",
    journey_4: "4. ನಿರ್ಬಂಧವಿಲ್ಲದ ಸುರಕ್ಷಿತ & ಸಮೃದ್ಧ ವಲಯ ಹುಡುಕಿ",
    journey_5: "5. ಆಯ್ಕೆ ಮಾಡಿದ ಪ್ರದೇಶಕ್ಕೆ ಸುರಕ್ಷಿತ ಮಾರ್ಗ ತೋರಿಸಿ",
    chips_header: "🧠 ಅರ್ಥೈಸಿಕೊಂಡ ಕಾರ್ಯಾಚರಣೆ ವಿವರಗಳು (ಬದಲಾಯಿಸಲು ಕ್ಲಿಕ್ ಮಾಡಿ):",
    chips_reset: "ಮರುಹೊಂದಿಸಿ",
    chip_location: "ಸ್ಥಳ",
    chip_departure: "ಹೊರಡುವ ಸಮಯ",
    chip_vessel: "ದೋಣಿ",
    chip_activity: "ಕಾರ್ಯ",
    chip_range: "ವ್ಯಾಪ್ತಿ",
    chip_constraints: "ನಿರ್ಬಂಧಗಳು",
    card_scenario_controls: "🎯 ಸನ್ನಿವೇಶ ನಿಯಂತ್ರಣ & ಪ್ರಶ್ನೆ",
    lbl_tide_station: "ಉಬ್ಬರವಿಳಿತ ಕೇಂದ್ರ (Tide Station)",
    lbl_latitude: "ಅಕ್ಷಾಂಶ (°N)",
    lbl_longitude: "ರೇಖಾಂಶ (°E)",
    lbl_vessel_class: "ದೋಣಿಯ ವರ್ಗ",
    lbl_dep_window: "ಹೊರಡುವ ಸಮಯಾವಧಿ",
    lbl_max_range: "ಗರಿಷ್ಠ ದೂರ (ಕಿ.ಮೀ)",
    opt_vessel_canoe: "ಸಾಂಪ್ರದಾಯಿಕ ದೋಣಿ (≤7 ಮೀ)",
    opt_vessel_motorized: "ಮೋಟಾರೀಕೃತ OBM (8–10 ಮೀ)",
    opt_vessel_trawler: "ಯಾಂತ್ರೀಕೃತ ಟ್ರಾಲರ್ (>12 ಮೀ)",
    opt_time_tomorrow_05am: "ನಾಳೆ ಬೆಳಿಗ್ಗೆ 05:00 AM (ಇಳಿಮುಖ ಉಬ್ಬರ)",
    opt_time_tomorrow_09am: "ನಾಳೆ ಬೆಳಿಗ್ಗೆ 09:00 AM (ಪೂರ್ಣ ಉಬ್ಬರ)",
    opt_time_tomorrow_02pm: "ನಾಳೆ ಮಧ್ಯಾಹ್ನ 02:00 PM",
    opt_time_today_now: "ಇಂದೇ ತಕ್ಷಣ ನಿರ್ಗಮನ",
    btn_run_decision_loop: "ಸಂಪೂರ್ಣ ನಿರ್ಧಾರ ಪರಿಶೀಲನೆ ಚಲಾಯಿಸಿ",
    card_orca_pipeline: "⚙️ ORCA 10-ಹಂತಗಳ ಪೈಪ್‌ಲೈನ್ ಎಂಜಿನ್",
    pipe_0: "ಪ್ರಶ್ನೆ ಸ್ವೀಕರಿಸಲಾಗಿದೆ",
    pipe_1: "ಉದ್ದೇಶ ಅರ್ಥೈಸಲಾಗಿದೆ",
    pipe_2: "ಕಾರ್ಯಯೋಜನೆ ಸಿದ್ಧವಾಗಿದೆ",
    pipe_3: "ಡೇಟಾ ಪಡೆಯಲಾಗಿದೆ",
    pipe_4: "ಮಾನಕೀಕರಣಗೊಂಡಿದೆ",
    pipe_5: "ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ",
    pipe_6: "ಸುರಕ್ಷತಾ ಮಿತಿ ಪರಿಶೀಲನೆ",
    pipe_7: "ಉತ್ತಮ ವಲಯ ಶ್ರೇಯಾಂಕ",
    pipe_8: "ದೃಢೀಕರಣ ಪೂರ್ಣಗೊಂಡಿದೆ",
    pipe_9: "ಸಲಹೆ ನೀಡಲಾಗಿದೆ",
    card_maritime_limits: "🗺️ ಕಡಲ ಗಡಿಗಳು & ಕರಾವಳಿ ರೇಖೆ",
    card_exec_rec: "🎯 ಪ್ರಮುಖ ನಿರ್ಧಾರ & ಶಿಫಾರಸು",
    status_standby: "ಸಿದ್ಧವಾಗಿದೆ",
    status_approved: "ಅನುಮೋದಿಸಲಾಗಿದೆ",
    status_rejected: "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ",
    status_reassess: "ಮರುಪರಿಶೀಲಿಸಿ",
    verdict_go: "ಹೌದು, ಪ್ರಯಾಣಿಸಬಹುದು (GO)",
    verdict_avoid: "ದಡದಲ್ಲೇ ಇರಿ (AVOID)",
    verdict_reassess: "ಮರುಪರಿಶೀಲಿಸಿ (REASSESS)",
    verdict_sub_go: "ಸುರಕ್ಷಿತ ಸಮುದ್ರ ಸ್ಥಿತಿ · ಭದ್ರತಾ ನಿಯಮಗಳು ಉತ್ತೀರ್ಣವಾಗಿವೆ",
    verdict_sub_avoid: "ದೋಣಿಯ ಸುರಕ್ಷತಾ ಮಿತಿ ಮೀರಿದೆ ಅಥವಾ ಚಂಡಮಾರುತ ಎಚ್ಚರಿಕೆ ಇದೆ",
    verdict_sub_reassess: "ಬೇರೆ ಸಮಯ ಅಥವಾ ವಲಯವನ್ನು ಪರಿಶೀಲಿಸಿ",
    dec_best_zone: "ಅತ್ಯುತ್ತಮ ಮೀನುಗಾರಿಕಾ ವಲಯ",
    dec_dep_window: "ಅತ್ಯುತ್ತಮ ಹೊರಡುವ ಸಮಯ",
    dec_safety_score: "ಸುರಕ್ಷತಾ ಅಂಕ",
    dec_fishing_value: "ಮೀನುಗಾರಿಕಾ ಮೌಲ್ಯ",
    dec_safest_route: "ಸುರಕ್ಷಿತ ಮಾರ್ಗ",
    dec_confidence: "ಮಾಹಿತಿ ನಿಖರತೆ",
    dec_why_label: "🔍 ಈ ನಿರ್ಧಾರಕ್ಕೆ ಕಾರಣವೇನು? (ಸಾಕ್ಷ್ಯಾಧಾರಿತ ವಿವರಣೆ)",
    card_map_title: "🗺️ ನಕ್ಷೆ & ಸುರಕ್ಷಿತ ಪಯಣ ಮಾರ್ಗ",
    btn_map_center: "⌖ ಕೇಂದ್ರ",
    btn_map_route: "ಮಾರ್ಗ",
    btn_map_hazards: "ಅಪಾಯ ವಲಯಗಳು",
    leg_boat: "ನಿಮ್ಮ ದೋಣಿ",
    leg_pfz: "ಸಂಭಾವ್ಯ PFZ ವಲಯ",
    leg_rec: "ಶಿಫಾರಸು ಮಾಡಿದ ವಲಯ",
    leg_danger: "ರಕ್ಷಿತ ಪ್ರದೇಶ (ಪ್ರವೇಶ ನಿಷೇಧ)",
    leg_safe_route: "ಸುರಕ್ಷಿತ ಮಾರ್ಗ",
    leg_avoided: "ತಪ್ಪಿಸಿದ ಅಪಾಯ ವಲಯ",
    metric_pfz: "PFZ ಸ್ಥಿತಿ",
    metric_sst: "ಸಮುದ್ರ ಮೇಲ್ಮೈ ತಾಪಮಾನ",
    metric_chla: "ಕ್ಲೋರೊಫಿಲ್-ಎ",
    metric_wave: "ಅಲೆಯ ಎತ್ತರ (Hs)",
    metric_tide: "ಉಬ್ಬರವಿಳಿತ ಸ್ಥಿತಿ",
    metric_safety_gate: "ಸುರಕ್ಷತಾ ಗೇಟ್",
    card_sva_title: "🚢 ಸಣ್ಣ ದೋಣಿ ಸಲಹೆ (SVA) — ಕಠಿಣ ಮಿತಿಗಳು",
    card_sat_title: "🛰️ ಉಪಗ್ರಹ ಉತ್ಪನ್ನಗಳು — EOS-06 / Oceansat-3",
    card_tide_title: "🌊 ಉಬ್ಬರವಿಳಿತ ಮುನ್ಸೂಚನೆ — INCOIS ಮಾದರಿ",
    card_weather_title: "⛈️ ಹವಾಮಾನ · ಮಿಂಚು · ಚಂಡಮಾರುತ ಎಚ್ಚರಿಕೆ",
    card_advisory_title: "🤖 ಬಹುಭಾಷಾ AI ಸಲಹೆ — ORCA ನಿರ್ಧಾರ",
    advisory_placeholder: "ಸಂಪೂರ್ಣ ವಿಶ್ಲೇಷಣೆಯನ್ನು ಚಲಾಯಿಸಿ ಅಥವಾ ಭಾರತೀಯ ಭಾಷೆಗಳಲ್ಲಿ ಸಲಹೆ ಪಡೆಯಿರಿ.",
    card_erddap_title: "📦 ERDDAP ಡಿಜಿಟಲ್ ಡೇಟಾಸೆಟ್",
    card_evidence_title: "🔍 ಸಾಕ್ಷ್ಯಾಧಾರ ಜಾಡು & ಡೇಟಾ ಪರಿಶೀಲನೆ",
    sva_clear_to_sail: "✅ ಸಮುದ್ರಯಾನಕ್ಕೆ ಸುರಕ್ಷಿತ",
    sva_do_not_sail: "🚫 ಪ್ರಯಾಣಿಸಬೇಡಿ (ದಡದಲ್ಲೇ ಇರಿ)",
    sva_max_wave: "ಗರಿಷ್ಠ ಅಲೆಯ ಎತ್ತರ",
    sva_max_wind: "ಗರಿಷ್ಠ ಗಾಳಿಯ ವೇಗ",
    sva_max_dist: "ಗರಿಷ್ಠ ದೂರ",
    sva_max_beaufort: "ಗರಿಷ್ಠ ಬ್ಯೂಫೋರ್ಟ್",
    sat_fish_prod: "ಉತ್ಪಾದಕತೆ",
    cyclone_no_active: "✓ ಸಕ್ರಿಯ ಚಂಡಮಾರುತವಿಲ್ಲ",
    lightning_risk: "ಮಿಂಚಿನ ಅಪಾಯ"
  },
  hi: {
    badge_agentic: "एजेंटिक AI",
    topbar_subtitle: "ORCA — महासागर जोखिम एवं तटीय परामर्श प्रणाली · SIH 2026",
    backend_live: "⬤ बैकएंड सक्रिय है",
    backend_offline: "⬤ बैकएंड ऑफ़लाइन है",
    chat_placeholder: "ORCA से पूछें: जैसे 'मेरे पास 5 मीटर की नाव है। क्या मैं कल सुबह 5 बजे मालपे से 30 किमी के भीतर मछली पकड़ने जा सकता हूँ?'",
    btn_analyze_query: "विश्लेषण करें",
    demo_journeys_label: "⚡ 5 प्रमुख डेमो यात्राएं:",
    journey_1: "1. क्या मैं कल सुबह सुरक्षित रूप से मछली पकड़ने जा सकता हूँ?",
    journey_2: "2. निकटतम उपयोगी PFZ कहाँ है?",
    journey_3: "3. मेरे आस-पास समुद्र की स्थिति कैसी है?",
    journey_4: "4. सुरक्षित और अप्रतिबंधित उत्पादक क्षेत्र खोजें",
    journey_5: "5. चयनित क्षेत्र के लिए सबसे सुरक्षित मार्ग दिखाएं",
    chips_header: "🧠 निकाली गई परिचालन समझ (बदलने के लिए क्लिक करें):",
    chips_reset: "रीसेट करें",
    chip_location: "स्थान",
    chip_departure: "प्रस्थान समय",
    chip_vessel: "नौका",
    chip_activity: "गतिविधि",
    chip_range: "सीमा",
    chip_constraints: "प्रतिबंध",
    card_scenario_controls: "🎯 परिदृश्य नियंत्रण एवं प्रश्न",
    lbl_tide_station: "ज्वार स्टेशन (Tide Station)",
    lbl_latitude: "अक्षांश (°N)",
    lbl_longitude: "देशांतर (°E)",
    lbl_vessel_class: "नौका श्रेणी",
    lbl_dep_window: "प्रस्थान समय",
    lbl_max_range: "अधिकतम सीमा (किमी)",
    opt_vessel_canoe: "पारंपरिक डोंगी (≤7 मी)",
    opt_vessel_motorized: "मोटराइज्ड क्राफ्ट (8–10 मी)",
    opt_vessel_trawler: "मैकेनाइज्ड ट्रॉलर (>12 मी)",
    opt_time_tomorrow_05am: "कल सुबह 05:00 AM (भाटा समय)",
    opt_time_tomorrow_09am: "कल सुबह 09:00 AM (ज्वार समय)",
    opt_time_tomorrow_02pm: "कल दोपहर 02:00 PM",
    opt_time_today_now: "आज तुरंत प्रस्थान",
    btn_run_decision_loop: "पूर्ण निर्णय चक्र चलाएं",
    card_orca_pipeline: "⚙️ ORCA 10-चरणीय पाइपलाइन इंजन",
    pipe_0: "प्रश्न प्राप्त हुआ",
    pipe_1: "उद्देश्य समझा गया",
    pipe_2: "योजना तैयार",
    pipe_3: "डेटा प्राप्त किया",
    pipe_4: "सामान्यीकृत किया",
    pipe_5: "विश्लेषण पूर्ण",
    pipe_6: "सुरक्षा सीमा जांच",
    pipe_7: "रैंकिंग पूर्ण",
    pipe_8: "सत्यापित",
    pipe_9: "सलाह वितरित",
    card_maritime_limits: "🗺️ समुद्री सीमाएं एवं बेसलाइन",
    card_exec_rec: "🎯 कार्यकारी अनुशंसा",
    status_standby: "स्टैंडबाय",
    status_approved: "स्वीकृत",
    status_rejected: "अस्वीकृत",
    status_reassess: "पुनर्मूल्यांकन",
    verdict_go: "यात्रा अनुकूल (GO)",
    verdict_avoid: "तट पर रहें (AVOID)",
    verdict_reassess: "पुनर्मूल्यांकन करें (REASSESS)",
    verdict_sub_go: "सुरक्षित समुद्री स्थिति · सुरक्षा द्वार पास हुआ",
    verdict_sub_avoid: "नौका सीमा से अधिक या गंभीर खतरा सक्रिय",
    verdict_sub_reassess: "वैकल्पिक प्रस्थान समय की समीक्षा करें",
    dec_best_zone: "सर्वश्रेष्ठ मत्स्य क्षेत्र",
    dec_dep_window: "सर्वोत्तम प्रस्थान समय",
    dec_safety_score: "सुरक्षा स्कोर",
    dec_fishing_value: "मत्स्य मूल्य",
    dec_safest_route: "सबसे सुरक्षित मार्ग",
    dec_confidence: "डेटा विश्वसनीयता",
    dec_why_label: "🔍 यह निर्णय क्यों? (साक्ष्य-आधारित स्पष्टीकरण)",
    card_map_title: "🗺️ संवादात्मक परिचालन मानचित्र एवं सुरक्षित मार्ग",
    btn_map_center: "⌖ केंद्र",
    btn_map_route: "मार्ग",
    btn_map_hazards: "खतरे",
    leg_boat: "प्रस्थान नौका",
    leg_pfz: "संभावित PFZ",
    leg_rec: "अनुशंसित PFZ",
    leg_danger: "प्रतिबंधित क्षेत्र (वर्जित)",
    leg_safe_route: "सुरक्षित मार्ग",
    leg_avoided: "बचाया गया खतरा",
    metric_pfz: "PFZ स्थिति",
    metric_sst: "समुद्र सतह तापमान",
    metric_chla: "क्लोरोफिल-ए",
    metric_wave: "लहर की ऊंचाई (Hs)",
    metric_tide: "ज्वार स्थिति",
    metric_safety_gate: "सुरक्षा द्वार",
    card_sva_title: "🚢 लघु नौका परामर्श (SVA) — सीमाएं",
    card_sat_title: "🛰️ उपग्रह उत्पाद — EOS-06 / Oceansat-3",
    card_tide_title: "🌊 ज्वार पूर्वानुमान — INCOIS मॉडल",
    card_weather_title: "⛈️ मौसम · बिजली · चक्रवात चेतावनी",
    card_advisory_title: "🤖 बहुभाषी AI सलाह — ORCA निर्णय",
    advisory_placeholder: "द्विभाषी निर्णय प्राप्त करने के लिए पूर्ण विश्लेषण चलाएं या भारतीय भाषाओं में पूछें।",
    card_erddap_title: "📦 ERDDAP मशीन-पठनीय डेटासेट",
    card_evidence_title: "🔍 साक्ष्य पथ एवं डेटा प्रमाणन",
    sva_clear_to_sail: "✅ नौकायन हेतु सुरक्षित",
    sva_do_not_sail: "🚫 नौकायन न करें (तट पर रहें)",
    sva_max_wave: "अधिकतम लहर ऊंचाई",
    sva_max_wind: "अधिकतम हवा गति",
    sva_max_dist: "अधिकतम दूरी",
    sva_max_beaufort: "अधिकतम ब्यूफोर्ट",
    sat_fish_prod: "उत्पादकता",
    cyclone_no_active: "✓ कोई सक्रिय चक्रवात नहीं",
    lightning_risk: "आकाशीय बिजली का जोखिम"
  },
  ta: {
    badge_agentic: "ஏஜென்டிக் AI",
    topbar_subtitle: "ORCA — கடல்சார் இடர் மற்றும் கடலோர எச்சரிக்கை அமைப்பு · SIH 2026",
    backend_live: "⬤ சர்வர் நேரலையில் உள்ளது",
    backend_offline: "⬤ சர்வர் ஆஃப்லைனில் உள்ளது",
    chat_placeholder: "ORCA விடம் கேளுங்கள்: எ.கா: 'என்னிடம் 5 மீ படகு உள்ளது. நாளை காலை 5 மணிக்கு மால்பேயில் இருந்து 30 கி.மீ தூரம் மீன்பிடிக்க செல்லலாமா?'",
    btn_analyze_query: "கேள்வியை ஆராய்க",
    demo_journeys_label: "⚡ 5 முக்கிய டெமோ பயணங்கள்:",
    journey_1: "1. நாளை காலை நான் பாதுகாப்பாக மீன்பிடிக்க செல்லலாமா?",
    journey_2: "2. அருகில் உள்ள பயனுள்ள PFZ எங்குள்ளது?",
    journey_3: "3. என்னைச் சுற்றியுள்ள கடல் நிலை எப்படி உள்ளது?",
    journey_4: "4. தடைசெய்யப்படாத பாதுகாப்பான மீன்பிடி பகுதியைக் கண்டறிக",
    journey_5: "5. தேர்ந்தெடுக்கப்பட்ட பகுதிக்கு பாதுகாப்பான வழியைக் காட்டுக",
    chips_header: "🧠 பெறப்பட்ட செயல்பாட்டு விவரங்கள் (மாற்ற கிளிக் செய்யவும்):",
    chips_reset: "மீட்டமை",
    chip_location: "இடம்",
    chip_departure: "புறப்படும் நேரம்",
    chip_vessel: "படகு",
    chip_activity: "செயல்பாடு",
    chip_range: "வரம்பு",
    chip_constraints: "கட்டுப்பாடுகள்",
    card_scenario_controls: "🎯 சூழல் கட்டுப்பாடுகள் & தேடல்",
    lbl_tide_station: "அலை நிலையம் (Tide Station)",
    lbl_latitude: "அட்சரேகை (°N)",
    lbl_longitude: "தீர்க்கரேகை (°E)",
    lbl_vessel_class: "படகு வகை",
    lbl_dep_window: "புறப்படும் நேரம்",
    lbl_max_range: "அதிகபட்ச தூரம் (கி.மீ)",
    opt_vessel_canoe: "பாரம்பரிய படகு (≤7 மீ)",
    opt_vessel_motorized: "இயந்திர படகு (8–10 மீ)",
    opt_vessel_trawler: "விசைப்படகு (>12 மீ)",
    opt_time_tomorrow_05am: "நாளை காலை 05:00 AM (வற்றுப் பெருக்கு)",
    opt_time_tomorrow_09am: "நாளை காலை 09:00 AM (முழு அலை)",
    opt_time_tomorrow_02pm: "நாளை பிற்பகல் 02:00 PM",
    opt_time_today_now: "இன்றே உடனடியாக புறப்படுதல்",
    btn_run_decision_loop: "முழு முடிவை செயல்படுத்துக",
    card_orca_pipeline: "⚙️ ORCA 10-படிநிலை குழாய் இயந்திரம்",
    pipe_0: "கேள்வி பெறப்பட்டது",
    pipe_1: "நோக்கம் உணரப்பட்டது",
    pipe_2: "திட்டம் உருவாக்கப்பட்டது",
    pipe_3: "தரவு பெறப்பட்டது",
    pipe_4: "ஒழுங்குபடுத்தப்பட்டது",
    pipe_5: "ஆராய்ச்சி முடிந்தது",
    pipe_6: "பாதுகாப்பு எல்லை சரிபார்ப்பு",
    pipe_7: "வரிசைப்படுத்தல்",
    pipe_8: "சரிபார்க்கப்பட்டது",
    pipe_9: "ஆலோசனை வழங்கப்பட்டது",
    card_maritime_limits: "🗺️ கடல் எல்லைகள்",
    card_exec_rec: "🎯 முக்கிய பரிந்துரை",
    status_standby: "காத்திருப்பு",
    status_approved: "அங்கீகரிக்கப்பட்டது",
    status_rejected: "நிராகரிக்கப்பட்டது",
    status_reassess: "மறுபரிசீலனை",
    verdict_go: "செல்லலாம் (GO)",
    verdict_avoid: "கரையில் இருங்கள் (AVOID)",
    verdict_reassess: "மறுபரிசீலனை செய்க (REASSESS)",
    verdict_sub_go: "பாதுகாப்பான கடல் நிலை · பாதுகாப்பு விதிகள் தேர்ச்சி",
    verdict_sub_avoid: "படகு வரம்பை மீறியது அல்லது சூறாவளி எச்சரிக்கை உள்ளது",
    verdict_sub_reassess: "மாற்று நேரத்தை தேர்வு செய்யவும்",
    dec_best_zone: "சிறந்த மீன்பிடி மண்டலம்",
    dec_dep_window: "சிறந்த புறப்படும் நேரம்",
    dec_safety_score: "பாதுகாப்பு மதிப்பெண்",
    dec_fishing_value: "மீன்பிடி மதிப்பு",
    dec_safest_route: "பாதுகாப்பான வழித்தடம்",
    dec_confidence: "தரவு நம்பகத்தன்மை",
    dec_why_label: "🔍 இந்த முடிவிற்கு காரணம் என்ன? (சான்றளிக்கப்பட்ட விளக்கம்)",
    card_map_title: "🗺️ கடல்சார் வரைபடம் & பாதுகாப்பான வழி",
    btn_map_center: "⌖ மையம்",
    btn_map_route: "வழி",
    btn_map_hazards: "அபாயங்கள்",
    leg_boat: "புறப்படும் படகு",
    leg_pfz: "PFZ பகுதி",
    leg_rec: "பரிந்துரைக்கப்பட்ட பகுதி",
    leg_danger: "தடைசெய்யப்பட்ட பகுதி",
    leg_safe_route: "பாதுகாப்பான வழி",
    leg_avoided: "தவிர்க்கப்பட்ட ஆபத்து",
    metric_pfz: "PFZ நிலை",
    metric_sst: "கடல் மேற்பரப்பு வெப்பநிலை",
    metric_chla: "குளோரோபில்-ஏ",
    metric_wave: "அலை உயரம் (Hs)",
    metric_tide: "அலை நிலை",
    metric_safety_gate: "பாதுகாப்பு வாயில்",
    card_sva_title: "🚢 சிறிய படகு ஆலோசனை (SVA)",
    card_sat_title: "🛰️ செயற்கைக்கோள் தரவு — EOS-06",
    card_tide_title: "🌊 அலை முன்னறிவிப்பு — INCOIS மாதிரி",
    card_weather_title: "⛈️ வானிலை · மின்னல் · புயல் எச்சரிக்கை",
    card_advisory_title: "🤖 பலமொழி AI ஆலோசனை — ORCA முடிவு",
    advisory_placeholder: "முழு ஆலோசனையைப் பெற பகுப்பாய்வை இயக்கவும்.",
    card_erddap_title: "📦 ERDDAP தரவுத்தொகுப்பு",
    card_evidence_title: "🔍 சான்று தடம் & தரவு தணிக்கை",
    sva_clear_to_sail: "✅ கடலுக்கு செல்லலாம்",
    sva_do_not_sail: "🚫 கடலுக்கு செல்ல வேண்டாம்",
    sva_max_wave: "அதிகபட்ச அலை உயரம்",
    sva_max_wind: "அதிகபட்ச காற்று வேகம்",
    sva_max_dist: "அதிகபட்ச தூரம்",
    sva_max_beaufort: "அதிகபட்ச பியூஃபோர்ட்",
    sat_fish_prod: "உற்பத்தித்திறன்",
    cyclone_no_active: "✓ புயல் எச்சரிக்கை இல்லை",
    lightning_risk: "மின்னல் ஆபத்து"
  },
  te: {
    badge_agentic: "ఏజెంటిక్ AI",
    topbar_subtitle: "ORCA — సముద్ర ప్రమాద & తీర హెచ్చరిక వ్యవస్థ · SIH 2026",
    backend_live: "⬤ సర్వర్ ప్రత్యక్షంగా ఉంది",
    backend_offline: "⬤ సర్వర్ ఆఫ్‌లైన్",
    chat_placeholder: "ORCA ని అడగండి: ఉదా: 'నా వద్ద 5 మీటర్ల పడవ ఉంది. రేపు ఉదయం 5 గంటలకు మాల్పే నుండి 30 కిమీ పరిధిలో చేపల వేటకు వెళ్ళవచ్చా?'",
    btn_analyze_query: "ప్రశ్నను విశ్లేషించండి",
    demo_journeys_label: "⚡ 5 ముఖ్యమైన డెమో ప్రయాణాలు:",
    journey_1: "1. రేపు ఉదయం నేను సురక్షితంగా చేపల వేటకు వెళ్ళవచ్చా?",
    journey_2: "2. సమీపంలో ఉన్న ఉపయోగకరమైన PFZ ఎక్కడ ఉంది?",
    journey_3: "3. నా సమీపంలోని సముద్ర పరిస్థితులు ఎలా ఉన్నాయి?",
    journey_4: "4. నిషేధించబడని సురక్షిత & ఉత్పాదక ప్రాంతాన్ని కనుగొనండి",
    journey_5: "5. ఎంచుకున్న ప్రాంతానికి సురక్షిత మార్గాన్ని చూపించండి",
    chips_header: "🧠 గుర్తించిన కార్యాచరణ వివరాలు (సవరించడానికి క్లిక్ చేయండి):",
    chips_reset: "రీసెట్ చేయండి",
    chip_location: "ప్రాంతం",
    chip_departure: "బయలుదేరే సమయం",
    chip_vessel: "పడవ",
    chip_activity: "కార్యకలాపం",
    chip_range: "పరిధి",
    chip_constraints: "పరిమితులు",
    card_scenario_controls: "🎯 దృష్టాంత నియంత్రణలు & ప్రశ్న",
    lbl_tide_station: "టైడ్ స్టేషన్ (Tide Station)",
    lbl_latitude: "అక్షాంశం (°N)",
    lbl_longitude: "రేఖాంశం (°E)",
    lbl_vessel_class: "పడవ తరగతి",
    lbl_dep_window: "బయలుదేరే సమయం",
    lbl_max_range: "గరిష్ట పరిధి (కిమీ)",
    opt_vessel_canoe: "సాంప్రదాయ పడవ (≤7 మీ)",
    opt_vessel_motorized: "మోటరైజ్డ్ క్రాఫ్ట్ (8–10 మీ)",
    opt_vessel_trawler: "మెకనైజ్డ్ ట్రాలర్ (>12 మీ)",
    opt_time_tomorrow_05am: "రేపు ఉదయం 05:00 AM",
    opt_time_tomorrow_09am: "రేపు ఉదయం 09:00 AM",
    opt_time_tomorrow_02pm: "రేపు మధ్యాహ్నం 02:00 PM",
    opt_time_today_now: "ఈరోజే వెంటనే ప్రయాణం",
    btn_run_decision_loop: "పూర్తి నిర్ణయాన్ని అమలు చేయండి",
    card_orca_pipeline: "⚙️ ORCA 10-దశల పైప్‌లైన్ ఇంజిన్",
    pipe_0: "ప్రశ్న స్వీకరించబడింది",
    pipe_1: "ఉద్దేశం గ్రహించబడింది",
    pipe_2: "ప్రణాళిక సిద్ధం",
    pipe_3: "డేటా పొందబడింది",
    pipe_4: "క్రమబద్ధీకరించబడింది",
    pipe_5: "విశ్లేషణ పూర్తయింది",
    pipe_6: "భద్రతా పరిమితి తనిఖీ",
    pipe_7: "శ్రేణి నిర్ణయం",
    pipe_8: "ధృవీకరించబడింది",
    pipe_9: "సలహా ఇవ్వబడింది",
    card_maritime_limits: "🗺️ సముద్ర సరిహద్దులు",
    card_exec_rec: "🎯 ముఖ్యమైన సిఫార్సు",
    status_standby: "సిద్ధంగా ఉంది",
    status_approved: "ఆమోదించబడింది",
    status_rejected: "తిరస్కరించబడింది",
    status_reassess: "పునఃపరిశీలించండి",
    verdict_go: "ప్రయాణించవచ్చు (GO)",
    verdict_avoid: "తీరంలోనే ఉండండి (AVOID)",
    verdict_reassess: "పునఃపరిశీలించండి (REASSESS)",
    verdict_sub_go: "సురక్షిత సముద్ర పరిస్థితి · భద్రతా నియమాలు ఆమోదించబడ్డాయి",
    verdict_sub_avoid: "పడవ పరిమితి దాటింది లేదా తుఫాను హెచ్చరిక ఉంది",
    verdict_sub_reassess: "మరొక సమయాన్ని పరిశీలించండి",
    dec_best_zone: "ఉత్తమ చేపల వేట జోన్",
    dec_dep_window: "ఉత్తమ ప్రయాణ సమయం",
    dec_safety_score: "భద్రతా స్కోరు",
    dec_fishing_value: "ఉత్పాదకత విలువ",
    dec_safest_route: "సురక్షిత మార్గం",
    dec_confidence: "డేటా విశ్వసనీయత",
    dec_why_label: "🔍 ఈ నిర్ణయానికి కారణం ఏమిటి? (సాక్ష్యాలతో కూడిన వివరణ)",
    card_map_title: "🗺️ సముద్ర పటం & సురక్షిత మార్గం",
    btn_map_center: "⌖ కేంద్రం",
    btn_map_route: "మార్గం",
    btn_map_hazards: "ప్రమాదాలు",
    leg_boat: "బయలుదేరే పడవ",
    leg_pfz: "PFZ ప్రాంతం",
    leg_rec: "సిఫార్సు చేయబడిన PFZ",
    leg_danger: "నిషేధిత ప్రాంతం",
    leg_safe_route: "సురక్షిత మార్గం",
    leg_avoided: "నివారించబడిన ప్రమాదం",
    metric_pfz: "PFZ స్థితి",
    metric_sst: "సముద్ర ఉపరితల ఉష్ణోగ్రత",
    metric_chla: "క్లోరోఫిల్-ఎ",
    metric_wave: "అలల ఎత్తు (Hs)",
    metric_tide: "పోటుపాటు స్థితి",
    metric_safety_gate: "భద్రతా గేట్",
    card_sva_title: "🚢 చిన్న పడవల సలహా (SVA)",
    card_sat_title: "🛰️ ఉపగ్రహ ఉత్పత్తులు — EOS-06",
    card_tide_title: "🌊 పోటుపాటుల సూచన — INCOIS నమూనా",
    card_weather_title: "⛈️ వాతావరణం · మెరుపులు · తుఫాను హెచ్చరికలు",
    card_advisory_title: "🤖 బహుభాషా AI సలహా — ORCA నిర్ణయం",
    advisory_placeholder: "పూర్తి విశ్లేషణను అమలు చేయండి లేదా భారతీయ భాషలలో అడగండి.",
    card_erddap_title: "📦 ERDDAP డేటాసెట్",
    card_evidence_title: "🔍 సాక్ష్యాల జాడ & డేటా ధృవీకరణ",
    sva_clear_to_sail: "✅ సముద్రయానానికి అనుకూలం",
    sva_do_not_sail: "🚫 ప్రయాణించవద్దు (తీరంలోనే ఉండండి)",
    sva_max_wave: "గరిష్ట అలల ఎత్తు",
    sva_max_wind: "గరిష్ట గాలి వేగం",
    sva_max_dist: "గరిష్ట దూరం",
    sva_max_beaufort: "గరిష్ట బ్యూఫోర్ట్",
    sat_fish_prod: "ఉత్పాదకత",
    cyclone_no_active: "✓ తుఫాను ముప్పు లేదు",
    lightning_risk: "మెరుపుల ముప్పు"
  },
  ml: {
    badge_agentic: "ഏജന്റിക് AI",
    topbar_subtitle: "ORCA — സമുദ്ര അപകട മുന്നറിയിപ്പ് സംവിധാനം · SIH 2026",
    backend_live: "⬤ സെർവർ തത്സമയം",
    backend_offline: "⬤ സെർവർ ഓഫ്ലൈൻ",
    chat_placeholder: "ORCA-യോട് ചോദിക്കുക: ഉദാ: 'എനിക്ക് 5 മീറ്റർ വള്ളമുണ്ട്. നാളെ രാവിലെ 5 മണിക്ക് മാൽപെയിൽ നിന്ന് 30 കി.മീ പരിധിയിൽ മീൻപിടിക്കാൻ പോകാമോ?'",
    btn_analyze_query: "വിശകലനം ചെയ്യുക",
    demo_journeys_label: "⚡ 5 പ്രധാന ഡെമോ യാത്രകൾ:",
    journey_1: "1. നാളെ രാവിലെ എനിക്ക് സുരക്ഷിതമായി മീൻപിടിക്കാൻ പോകാമോ?",
    journey_2: "2. ഏറ്റവും അടുത്തുള്ള ഉപയോഗപ്രദമായ PFZ എവിടെയാണ്?",
    journey_3: "3. എന്റെ സമീപത്തെ സമുദ്രാവസ്ഥ എങ്ങനെയാണ്?",
    journey_4: "4. നിരോധിതമല്ലാത്ത സുരക്ഷിതമായ മേഖല കണ്ടെത്തുക",
    journey_5: "5. തിരഞ്ഞെടുത്ത സ്ഥലത്തേക്കുള്ള ഏറ്റവും സുരക്ഷിതമായ വഴി കാണിക്കുക",
    chips_header: "🧠 തിരിച്ചറിഞ്ഞ പ്രവർത്തന വിവരങ്ങൾ (മാറ്റാൻ ക്ലിക്ക് ചെയ്യുക):",
    chips_reset: "പുനഃക്രമീകരിക്കുക",
    chip_location: "സ്ഥലം",
    chip_departure: "പുറപ്പെടുന്ന സമയം",
    chip_vessel: "ബോട്ട്",
    chip_activity: "പ്രവർത്തനം",
    chip_range: "പരിധി",
    chip_constraints: "നിയന്ത്രണങ്ങൾ",
    card_scenario_controls: "🎯 സാഹചര്യ നിയന്ത്രണങ്ങൾ",
    lbl_tide_station: "വേലിയേറ്റ നിലയം (Tide Station)",
    lbl_latitude: "അക്ഷാംശം (°N)",
    lbl_longitude: "രേഖാംശം (°E)",
    lbl_vessel_class: "ബോട്ട് തരം",
    lbl_dep_window: "പുറപ്പെടുന്ന സമയം",
    lbl_max_range: "പരമാവധി ദൂരം (കി.മീ)",
    opt_vessel_canoe: "പരമ്പരാഗത വള്ളം (≤7 മീ)",
    opt_vessel_motorized: "മോട്ടോർ ബോട്ട് (8–10 മീ)",
    opt_vessel_trawler: "ട്രോളർ (>12 മീ)",
    opt_time_tomorrow_05am: "നാളെ രാവിലെ 05:00 AM",
    opt_time_tomorrow_09am: "നാളെ രാവിലെ 09:00 AM",
    opt_time_tomorrow_02pm: "നാളെ ഉച്ചയ്ക്ക് 02:00 PM",
    opt_time_today_now: "ഇന്ന് ഉടനടി പുറപ്പെടുക",
    btn_run_decision_loop: "പൂർണ്ണ തീരുമാനം നടപ്പിലാക്കുക",
    card_orca_pipeline: "⚙️ ORCA 10-ഘട്ട പൈപ്പ്‌ലൈൻ എഞ്ചിൻ",
    pipe_0: "ചോദ്യം ലഭിച്ചു",
    pipe_1: "ലക്ഷ്യം മനസ്സിലാക്കി",
    pipe_2: "പദ്ധതി തയ്യാറാക്കി",
    pipe_3: "വിവരങ്ങൾ ശേഖരിച്ചു",
    pipe_4: "ക്രമീകരിച്ചു",
    pipe_5: "വിശകലനം പൂർത്തിയായി",
    pipe_6: "സുരക്ഷ പരിശോധിച്ചു",
    pipe_7: "റാങ്കിംഗ് നൽകി",
    pipe_8: "സ്ഥിരീകരിച്ചു",
    pipe_9: "ഉപദേശം നൽകി",
    card_maritime_limits: "🗺️ സമുദ്ര അതിർത്തികൾ",
    card_exec_rec: "🎯 പ്രധാന ശുപാർശ",
    status_standby: "സ്റ്റാൻഡ്ബൈ",
    status_approved: "അംഗീകരിച്ചു",
    status_rejected: "നിരസിച്ചു",
    status_reassess: "പുനഃപരിശോധിക്കുക",
    verdict_go: "യാത്ര പോകാം (GO)",
    verdict_avoid: "തീരത്ത് തുടരുക (AVOID)",
    verdict_reassess: "പുനഃപരിശോധിക്കുക (REASSESS)",
    verdict_sub_go: "സുരക്ഷിതമായ സമുദ്രാവസ്ഥ · സുരക്ഷാ അനുമതി ലഭിച്ചു",
    verdict_sub_avoid: "ബോട്ടിന്റെ പരിധി കവിഞ്ഞു അല്ലെങ്കിൽ ചുഴലിക്കാറ്റ് മുന്നറിയിപ്പ് ഉണ്ട്",
    verdict_sub_reassess: "മറ്റൊരു സമയം പരിശോധിക്കുക",
    dec_best_zone: "മികച്ച മത്സ്യബന്ധന മേഖല",
    dec_dep_window: "അനുയോജ്യമായ സമയം",
    dec_safety_score: "സുരക്ഷാ സ്കോർ",
    dec_fishing_value: "മത്സ്യമൂല്യം",
    dec_safest_route: "സുരക്ഷിത പാത",
    dec_confidence: "വിശ്വാസ്യത",
    dec_why_label: "🔍 ഈ തീരുമാനത്തിന് പിന്നിലെ കാരണം? (തെളിവ് സഹിതം)",
    card_map_title: "🗺️ സമുദ്ര ഭൂപടവും സുരക്ഷിത പാതയും",
    btn_map_center: "⌖ കേന്ദ്രം",
    btn_map_route: "പാത",
    btn_map_hazards: "അപകടങ്ങൾ",
    leg_boat: "നിങ്ങളുടെ ബോട്ട്",
    leg_pfz: "PFZ മേഖല",
    leg_rec: "ശുപാർശ ചെയ്ത മേഖല",
    leg_danger: "നിരോധിത മേഖല",
    leg_safe_route: "സുരക്ഷിത പാത",
    leg_avoided: "ഒഴിവാക്കിയ അപകടം",
    metric_pfz: "PFZ നില",
    metric_sst: "സമുദ്രോപരിതല താപനില",
    metric_chla: "ക്ലോറോഫിൽ-എ",
    metric_wave: "തിരമാല ഉയരം (Hs)",
    metric_tide: "വേലിയേറ്റ നില",
    metric_safety_gate: "സുരക്ഷാ ഗേറ്റ്",
    card_sva_title: "🚢 ചെറുവള്ളങ്ങൾക്കുള്ള ഉപദേശം (SVA)",
    card_sat_title: "🛰️ ഉപഗ്രഹ വിവരങ്ങൾ — EOS-06",
    card_tide_title: "🌊 വേലിയേറ്റ പ്രവചനം — INCOIS മാതൃക",
    card_weather_title: "⛈️ കാലാവസ്ഥ · മിന്നൽ · ചുഴലിക്കാറ്റ് മുന്നറിയിപ്പുകൾ",
    card_advisory_title: "🤖 ബഹുഭാഷാ AI ഉപദേശം — ORCA",
    advisory_placeholder: "പൂർണ്ണ വിവരങ്ങൾ ലഭിക്കുന്നതിന് വിശകലനം നടത്തുക.",
    card_erddap_title: "📦 ERDDAP ഡാറ്റാസെറ്റ്",
    card_evidence_title: "🔍 ഡാറ്റാ തെളിവുകളും പരിശോധനയും",
    sva_clear_to_sail: "✅ കടലിൽ പോകാം",
    sva_do_not_sail: "🚫 കടലിൽ പോകരുത് (തീരത്ത് തുടരുക)",
    sva_max_wave: "പരമാവധി തിരമാല ഉയരം",
    sva_max_wind: "പരമാവധി കാറ്റിന്റെ വേഗത",
    sva_max_dist: "പരമാവധി ദൂരം",
    sva_max_beaufort: "പരമാവധി ബ്യൂഫോർട്ട്",
    sat_fish_prod: "ഉൽപ്പാദനക്ഷമത",
    cyclone_no_active: "✓ ചുഴലിക്കാറ്റ് ഭീഷണിയില്ല",
    lightning_risk: "മിന്നൽ സാധ്യത"
  }
};

// Safe fallback for other Indian languages (Marathi, Gujarati, Bengali, Odia)
['mr', 'gu', 'bn', 'or'].forEach(l => {
  I18N_TRANSLATIONS[l] = Object.assign({}, I18N_TRANSLATIONS['hi']);
});

// Translation helper with English fallback
function t(key, defaultVal = '') {
  const lang = currentLanguage || 'en';
  if (I18N_TRANSLATIONS[lang] && I18N_TRANSLATIONS[lang][key] !== undefined) {
    return I18N_TRANSLATIONS[lang][key];
  }
  if (I18N_TRANSLATIONS['en'] && I18N_TRANSLATIONS['en'][key] !== undefined) {
    return I18N_TRANSLATIONS['en'][key];
  }
  return defaultVal || key;
}

// ─── APPLY GLOBAL LANGUAGE DYNAMICALLY (ISSUE 2 RESOLUTION) ───────────────────
function applyLanguage(lang) {
  currentLanguage = lang || 'en';
  try {
    localStorage.setItem('orca_language', currentLanguage);
  } catch (e) {}

  // Update all elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const trans = t(key);
    if (trans) el.textContent = trans;
  });

  // Update input placeholders
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    const trans = t(key);
    if (trans) el.placeholder = trans;
  });

  // Update titles/tooltips
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    const trans = t(key);
    if (trans) el.title = trans;
  });

  // Update pipeline step labels in current state
  refreshPipelineStepLabels();

  // Update primary button
  const analyzeBtn = document.getElementById('btn-analyze');
  if (analyzeBtn) {
    analyzeBtn.innerHTML = `⚓ <span>${t('btn_run_decision_loop')}</span>`;
  }

  // Update status badge
  const serverBadge = document.getElementById('server-status-badge');
  if (serverBadge) {
    const isLive = serverBadge.classList.contains('pill-green');
    serverBadge.textContent = isLive ? t('backend_live') : t('backend_offline');
  }

  // Update SVA panel labels if rendered
  refreshSVALabels();
}

function refreshPipelineStepLabels() {
  const stepKeys = [
    'pipe_0', 'pipe_1', 'pipe_2', 'pipe_3', 'pipe_4',
    'pipe_5', 'pipe_6', 'pipe_7', 'pipe_8', 'pipe_9'
  ];
  stepKeys.forEach((k, i) => {
    const el = document.getElementById(`step-${i}`);
    if (el) {
      const isDone = el.classList.contains('step-done');
      const isActive = el.classList.contains('step-active');
      const num = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩'][i];
      const icon = isDone ? '✓ ' : (isActive ? '⟳ ' : '');
      el.textContent = `${num} ${icon}${t(k)}`;
    }
  });
}

function refreshSVALabels() {
  // Translate dynamically rendered labels in SVA
  document.querySelectorAll('.sva-limit-key').forEach(el => {
    const txt = el.textContent.trim().toLowerCase();
    if (txt.includes('wave')) el.textContent = t('sva_max_wave');
    else if (txt.includes('wind')) el.textContent = t('sva_max_wind');
    else if (txt.includes('distance')) el.textContent = t('sva_max_dist');
    else if (txt.includes('beaufort')) el.textContent = t('sva_max_beaufort');
  });
}

function onLanguageChange() {
  const select = document.getElementById('lang-select');
  const selectedLang = select ? select.value : 'en';
  
  // Instantly apply global UI language across entire page (pure client-side, no API call)
  applyLanguage(selectedLang);
  
  showToast(`🌐 ${select ? select.options[select.selectedIndex].text : selectedLang} applied across entire dashboard.`);
  
  // NOTE: We intentionally do NOT call runFullAnalysis() here.
  // The full pipeline is already cached from the last query. Re-running it just to
  // change the display language would waste a full backend round-trip.
  // The advisory panel will use the new language on the next user query.
}

// ─── Clock ─────────────────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  const utc = now.toUTCString().slice(17, 25);
  const el = document.getElementById('time-badge');
  if (el) el.textContent = `${utc} UTC`;
}
setInterval(updateClock, 1000);
updateClock();

// ─── Server Status ──────────────────────────────────────────────────────────────
async function checkServerStatus() {
  const badge = document.getElementById('server-status-badge');
  try {
    const r = await fetch(`${API}/api/status`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) {
      badge.textContent = t('backend_live');
      badge.className = 'pill pill-green';
    } else throw new Error();
  } catch {
    badge.textContent = t('backend_offline');
    badge.className = 'pill';
    badge.style.background = 'rgba(255,68,68,0.15)';
    badge.style.color = '#ff4444';
    badge.style.border = '1px solid rgba(255,68,68,0.3)';
  }
}
checkServerStatus();

// ─── Toast ──────────────────────────────────────────────────────────────────────
function showToast(msg, duration = 3500) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), duration);
}

// ─── Pipeline Step Animations ───────────────────────────────────────────────────
function setStep(i, state) {
  const el = document.getElementById(`step-${i}`);
  if (el) {
    el.className = `step step-${state}`;
    const icons = { done: '✓ ', active: '⟳ ', error: '✗ ', idle: '' };
    const num = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩'][i];
    el.textContent = `${num} ${icons[state]}${t(`pipe_${i}`)}`;
  }
}

function resetPipeline() {
  for (let i = 2; i < 10; i++) setStep(i, 'idle');
}

async function animatePipeline(callback, delay = 250) {
  resetPipeline();
  for (let i = 2; i < 10; i++) {
    setStep(i, 'active');
    await sleep(delay);
    setStep(i, 'done');
  }
  if (callback) callback();
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ─── Fetch helpers ──────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const r = await fetch(`${API}${path}`, options);
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: `HTTP ${r.status}` }));
    throw new Error(err.detail || `HTTP ${r.status}`);
  }
  return r.json();
}

// ─── TIDE STATION ↔ MAP SYNCHRONIZATION (ISSUE 1 RESOLUTION) ───────────────────
/**
 * Single Source of Truth change handler:
 * When user selects a station, immediately updates:
 * 1. Station selection
 * 2. Lat/Lon coordinate inputs
 * 3. Map center & boat marker with smooth pan
 * 4. Understanding chips
 * 5. Tide harmonic forecast & all marine analytics
 * 6. Executes 10-step decision loop for the new location
 */
function onTideStationChange() {
  const stationSelect = document.getElementById('inp-station');
  if (!stationSelect) return;
  const stationName = stationSelect.value;
  const stationData = TIDE_STATIONS_REGISTRY[stationName];

  if (!stationData || typeof stationData.lat !== 'number' || typeof stationData.lon !== 'number') {
    showToast(`⚠️ Error: Invalid or missing coordinates for Tide Station '${stationName}'.`, 5000);
    return;
  }

  // 1. Update coordinate inputs
  document.getElementById('inp-lat').value = stationData.lat;
  document.getElementById('inp-lon').value = stationData.lon;

  // 2. Update understanding chip for Location
  const chipLoc = document.getElementById('chip-val-loc');
  if (chipLoc) {
    chipLoc.textContent = `${stationData.name} (${stationData.lat}°N, ${stationData.lon}°E)`;
  }

  // 3. Update Leaflet Map immediately: move center and re-position departure boat marker
  if (leafletMap) {
    leafletMap.setView([stationData.lat, stationData.lon], 9, { animate: true, duration: 1.0 });

    // Replace old boat marker cleanly
    if (mapLayers.boat) {
      leafletMap.removeLayer(mapLayers.boat);
    }
    const boatIcon = L.divIcon({
      className: 'custom-map-boat',
      html: `<div style="background:#00f2ff;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 0 16px #00f2ff;border:2px solid #fff;font-size:14px;">🚤</div>`,
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });
    mapLayers.boat = L.marker([stationData.lat, stationData.lon], { icon: boatIcon })
      .addTo(leafletMap)
      .bindPopup(`<strong>📍 Departure Station: ${stationData.label}</strong><br/>Coords: ${stationData.lat}°N, ${stationData.lon}°E`)
      .openPopup();
  }

  showToast(`⚓ Selected Tide Station: ${stationData.label}. Updating operational map & decision loop...`, 4000);

  // 4. Immediately trigger full analysis for this new station location without full page reload
  runFullAnalysis();
}

function onCoordsChange() {
  const lat = parseFloat(document.getElementById('inp-lat').value);
  const lon = parseFloat(document.getElementById('inp-lon').value);

  if (isNaN(lat) || isNaN(lon)) return;

  // Check if matches a known station
  for (const [sName, sData] of Object.entries(TIDE_STATIONS_REGISTRY)) {
    if (Math.abs(sData.lat - lat) < 0.1 && Math.abs(sData.lon - lon) < 0.1) {
      document.getElementById('inp-station').value = sName;
      break;
    }
  }

  const chipLoc = document.getElementById('chip-val-loc');
  if (chipLoc) {
    chipLoc.textContent = `Custom (${lat}°N, ${lon}°E)`;
  }

  if (leafletMap) {
    leafletMap.setView([lat, lon], 9, { animate: true });
  }

  runFullAnalysis();
}

// ─── LEAFLET OPERATIONAL MAP (P0 Requirement) ──────────────────────────────────
function initOperationalMap() {
  const container = document.getElementById('operational-map');
  if (!container || leafletMap) return;

  const currentStation = TIDE_STATIONS_REGISTRY[document.getElementById('inp-station')?.value || 'Malpe'] || TIDE_STATIONS_REGISTRY['Malpe'];

  leafletMap = L.map('operational-map', {
    center: [currentStation.lat, currentStation.lon],
    zoom: 9,
    zoomControl: true,
    attributionControl: false
  });

  // Authoritative Oceanographic Basemap (Bathymetry, Depth Contours & Marine Features)
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 13,
    attribution: 'Esri, GEBCO, NOAA'
  }).addTo(leafletMap);

  L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(leafletMap);
}

function clearMapLayers() {
  if (!leafletMap) return;
  if (mapLayers.boat) leafletMap.removeLayer(mapLayers.boat);
  mapLayers.pfzMarkers.forEach(m => leafletMap.removeLayer(m));
  mapLayers.pfzMarkers = [];
  if (mapLayers.recTarget) leafletMap.removeLayer(mapLayers.recTarget);
  if (mapLayers.recCircle) leafletMap.removeLayer(mapLayers.recCircle);
  if (mapLayers.safeRoute) leafletMap.removeLayer(mapLayers.safeRoute);
  if (mapLayers.blockedRoute) leafletMap.removeLayer(mapLayers.blockedRoute);
  mapLayers.hazardCircles.forEach(c => leafletMap.removeLayer(c));
  mapLayers.hazardCircles = [];
  mapLayers.hazardMarkers.forEach(m => leafletMap.removeLayer(m));
  mapLayers.hazardMarkers = [];
}

function renderCartography(carto) {
  if (!leafletMap) initOperationalMap();
  clearMapLayers();

  if (!carto || !carto.geojson || !carto.geojson.features) return;

  const features = carto.geojson.features;
  const boundsCoords = [];

  features.forEach(feat => {
    const props = feat.properties || {};
    const geom = feat.geometry || {};
    const type = props.type;

    if (type === 'USER_BASE_LOCATION') {
      const [lon, lat] = geom.coordinates;
      boundsCoords.push([lat, lon]);
      const boatIcon = L.divIcon({
        className: 'custom-map-boat',
        html: `<div style="background:#00f2ff;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 0 16px #00f2ff;border:2px solid #fff;font-size:14px;">🚤</div>`,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });
      mapLayers.boat = L.marker([lat, lon], { icon: boatIcon })
        .addTo(leafletMap)
        .bindPopup(`<strong>${props.title}</strong><br/>Vessel: ${props.vessel}<br/>Gate: ${props.safety_status}`);
    }

    else if (type === 'PFZ_CANDIDATE') {
      const [lon, lat] = geom.coordinates;
      boundsCoords.push([lat, lon]);
      const color = props.color || '#10b981';
      const m = L.circleMarker([lat, lon], {
        radius: 7,
        fillColor: color,
        color: '#fff',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.8
      }).addTo(leafletMap).bindPopup(`<strong>${props.title}</strong><br/>Chlorophyll: ${props.chlorophyll}<br/>SST: ${props.sst}<br/>Productivity: ${props.productivity_score}/100`);
      mapLayers.pfzMarkers.push(m);
    }

    else if (type === 'RECOMMENDED_PFZ_ZONE') {
      const [lon, lat] = geom.coordinates;
      boundsCoords.push([lat, lon]);
      const targetIcon = L.divIcon({
        className: 'custom-map-rec',
        html: `<div style="background:#22c55e;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 0 18px #22c55e;border:2.5px solid #fff;font-size:15px;">🎯</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });
      mapLayers.recTarget = L.marker([lat, lon], { icon: targetIcon })
        .addTo(leafletMap)
        .bindPopup(`<strong>${props.title}</strong><br/>Dist: ${props.distance_km} km<br/>Chlorophyll: ${props.chlorophyll}<br/>SST: ${props.sst}<br/>Species: ${props.species}`);
    }

    else if (type === 'PFZ_PERIMETER') {
      const latlngs = geom.coordinates[0].map(c => [c[1], c[0]]);
      mapLayers.recCircle = L.polygon(latlngs, {
        color: '#22c55e',
        weight: 2,
        fillColor: '#22c55e',
        fillOpacity: props.fill_opacity || 0.2
      }).addTo(leafletMap);
    }

    else if (type === 'RESTRICTED_AVOIDANCE_GEOFENCE') {
      const latlngs = geom.coordinates[0].map(c => [c[1], c[0]]);
      const poly = L.polygon(latlngs, {
        color: '#ef4444',
        weight: 2,
        fillColor: '#ef4444',
        fillOpacity: props.fill_opacity || 0.35,
        dashArray: '4, 4'
      }).addTo(leafletMap).bindPopup(`<strong>${props.title}</strong><br/>Restriction: ${props.restriction_level}<br/>Basis: ${props.legal_basis}`);
      mapLayers.hazardCircles.push(poly);
    }

    else if (type === 'RESTRICTED_CENTER_PIN') {
      const [lon, lat] = geom.coordinates;
      const warnIcon = L.divIcon({
        className: 'custom-hazard-pin',
        html: `<div style="font-size:16px;">⛔</div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });
      const m = L.marker([lat, lon], { icon: warnIcon }).addTo(leafletMap).bindPopup(`<strong>${props.title}</strong>`);
      mapLayers.hazardMarkers.push(m);
    }

    else if (type === 'SAFE_NAVIGATION_COURSE') {
      const latlngs = geom.coordinates.map(c => [c[1], c[0]]);
      latlngs.forEach(ll => boundsCoords.push(ll));
      mapLayers.safeRoute = L.polyline(latlngs, {
        color: '#00f2ff',
        weight: 4,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(leafletMap).bindPopup(`<strong>${props.title}</strong><br/>ETA: ${props.transit_time_hours} hours<br/>Detour Active: ${props.is_detour ? 'Yes (Bypassing MPAs)' : 'Direct'}`);
    }

    else if (type === 'AVOIDED_DIRECT_SEGMENT') {
      const latlngs = geom.coordinates.map(c => [c[1], c[0]]);
      mapLayers.blockedRoute = L.polyline(latlngs, {
        color: '#ef4444',
        weight: 2.5,
        opacity: 0.8,
        dashArray: '6, 6'
      }).addTo(leafletMap).bindPopup(`<strong>${props.title}</strong><br/>${props.warning}`);
    }
  });

  if (boundsCoords.length > 1) {
    leafletMap.fitBounds(boundsCoords, { padding: [40, 40], maxZoom: 10 });
  }
}

function resetMapView() {
  if (leafletMap) {
    const lat = parseFloat(document.getElementById('inp-lat').value) || 13.35;
    const lon = parseFloat(document.getElementById('inp-lon').value) || 74.70;
    leafletMap.setView([lat, lon], 9, { animate: true });
  }
}

function toggleMapLayer(layerType) {
  if (!leafletMap) return;
  if (layerType === 'route' && mapLayers.safeRoute) {
    if (leafletMap.hasLayer(mapLayers.safeRoute)) {
      leafletMap.removeLayer(mapLayers.safeRoute);
      if (mapLayers.blockedRoute) leafletMap.removeLayer(mapLayers.blockedRoute);
    } else {
      leafletMap.addLayer(mapLayers.safeRoute);
      if (mapLayers.blockedRoute) leafletMap.addLayer(mapLayers.blockedRoute);
    }
  } else if (layerType === 'hazards') {
    mapLayers.hazardCircles.forEach(c => {
      if (leafletMap.hasLayer(c)) leafletMap.removeLayer(c);
      else leafletMap.addLayer(c);
    });
  }
}

// ─── DECISION PACKAGE RENDERING (P0 & P1) ──────────────────────────────────────
function renderDecisionPackage(pkg) {
  if (!pkg) return;

  const verdictBadge = document.getElementById('dec-verdict-badge');
  const verdictText = document.getElementById('dec-verdict-text');
  const verdictSub = document.getElementById('dec-verdict-sub');
  const statusTag = document.getElementById('dec-status-tag');
  const verdictIcon = document.getElementById('dec-verdict-icon');

  const verdict = pkg.verdict || 'GO';
  if (verdict === 'GO') {
    verdictBadge.className = 'verdict-badge verdict-go';
    verdictText.textContent = t('verdict_go');
    verdictSub.textContent = t('verdict_sub_go');
    verdictIcon.textContent = '✅';
    statusTag.textContent = t('status_approved');
    statusTag.style.color = '#22c55e';
    statusTag.style.borderColor = 'rgba(34,197,94,0.3)';
    statusTag.style.background = 'rgba(34,197,94,0.15)';
  } else if (verdict === 'AVOID') {
    verdictBadge.className = 'verdict-badge verdict-avoid';
    verdictText.textContent = t('verdict_avoid');
    verdictSub.textContent = t('verdict_sub_avoid');
    verdictIcon.textContent = '🚫';
    statusTag.textContent = t('status_rejected');
    statusTag.style.color = '#ef4444';
    statusTag.style.borderColor = 'rgba(239,68,68,0.3)';
    statusTag.style.background = 'rgba(239,68,68,0.15)';
  } else {
    verdictBadge.className = 'verdict-badge verdict-reassess';
    verdictText.textContent = t('verdict_reassess');
    verdictSub.textContent = t('verdict_sub_reassess');
    verdictIcon.textContent = '⚠️';
    statusTag.textContent = t('status_reassess');
    statusTag.style.color = '#f59e0b';
    statusTag.style.borderColor = 'rgba(245,158,11,0.3)';
    statusTag.style.background = 'rgba(245,158,11,0.15)';
  }

  // Update metrics in grid
  document.getElementById('dec-best-zone').textContent = pkg.best_zone || 'None';
  document.getElementById('dec-best-window').textContent = pkg.best_window || '--';
  document.getElementById('dec-safety-score').textContent = `${pkg.safety_score ?? '--'} / 100`;
  document.getElementById('dec-fish-score').textContent = `${pkg.fishing_value ?? '--'} / 100`;
  document.getElementById('dec-route-km').textContent = `${pkg.route_km ?? '--'} km (~${pkg.transit_time_hours ?? '--'}h)`;
  document.getElementById('dec-confidence').textContent = `${pkg.confidence ?? 0.91} (High)`;

  // Update concise explanation
  document.getElementById('dec-why-text').textContent = pkg.why || 'Analysis completed.';

  // Update strip risk card
  setMetric('mc-risk-val', `${pkg.safety_score}/100`);
  const mc = document.getElementById('mc-risk');
  if (mc) mc.className = `metric-card ${verdict === 'GO' ? 'safe' : (verdict === 'AVOID' ? 'danger' : 'warn')}`;
}

// ─── UNDERSTANDING CHIPS RENDERING (P0) ────────────────────────────────────────
const CHIP_ID_MAP = {
  location: 'chip-val-loc',
  location_name: 'chip-val-loc',
  time: 'chip-val-time',
  departure_time: 'chip-val-time',
  vessel: 'chip-val-vessel',
  vessel_type: 'chip-val-vessel',
  activity: 'chip-val-act',
  range: 'chip-val-range',
  range_km: 'chip-val-range',
  constraints: 'chip-val-const'
};

function renderUnderstandingChips(chips) {
  const container = document.getElementById('understanding-chips');
  if (!container || !chips) return;

  container.innerHTML = chips.map(c => {
    const spanId = CHIP_ID_MAP[c.id] || CHIP_ID_MAP[c.raw_key] || `chip-val-${c.id}`;
    return `
      <div class="chip" onclick="editChip('${c.raw_key}')" title="Click to modify parameter">
        ${t('chip_' + c.id, c.label)}: <strong id="${spanId}">${c.value}</strong> ✎
      </div>
    `;
  }).join('');
}

function editChip(key) {
  const normalizedKey = key ? key.toLowerCase() : '';
  let promptMsg = `Modify ${key.replace('_', ' ')}:`;
  let currentVal = '';

  if (normalizedKey === 'location' || normalizedKey === 'location_name') {
    currentVal = prompt(`${promptMsg} (e.g., Malpe, Mangalore, Karwar, Kochi, Chennai)`, 'Malpe');
    if (currentVal) submitChatMessage(`Set location to ${currentVal}`);
  } else if (normalizedKey === 'time' || normalizedKey === 'departure_time') {
    currentVal = prompt(`${promptMsg} (e.g., Tomorrow 05:00 AM, Tomorrow 09:00 AM)`, 'Tomorrow 09:00 AM');
    if (currentVal) submitChatMessage(`What if I leave at ${currentVal}?`);
  } else if (normalizedKey === 'vessel' || normalizedKey === 'vessel_type') {
    currentVal = prompt(`${promptMsg} (canoe, motorized, trawler)`, 'motorized');
    if (currentVal) submitChatMessage(`Change vessel to ${currentVal}`);
  } else if (normalizedKey === 'range' || normalizedKey === 'range_km') {
    currentVal = prompt(`${promptMsg} in km:`, '40');
    if (currentVal) submitChatMessage(`Set maximum search range to ${currentVal} km`);
  } else if (normalizedKey === 'activity') {
    currentVal = prompt(`${promptMsg} (Fishing, Navigation, Tourism)`, 'Fishing');
    if (currentVal) submitChatMessage(`Set activity to ${currentVal}`);
  } else if (normalizedKey === 'constraints') {
    currentVal = prompt(`${promptMsg} (Avoid MPAs, Strict wave threshold)`, 'Avoid MPAs');
    if (currentVal) submitChatMessage(`Constraints: ${currentVal}`);
  } else {
    currentVal = prompt(promptMsg, '');
    if (currentVal) submitChatMessage(`Set ${key} to ${currentVal}`);
  }
}

function resetScenario() {
  document.getElementById('inp-station').value = 'Malpe';
  document.getElementById('inp-lat').value = 13.35;
  document.getElementById('inp-lon').value = 74.70;
  document.getElementById('inp-vessel').value = 'motorized_craft';
  document.getElementById('inp-time-select').value = 'Tomorrow 05:00 AM';
  document.getElementById('inp-range').value = 35;
  activeSessionId = 'orca_session_' + Date.now();
  
  // Clear input box and reset pills
  const inputEl = document.getElementById('chat-input');
  if (inputEl) inputEl.value = '';
  document.querySelectorAll('.journey-pill').forEach(p => p.classList.remove('active'));

  // Hide chat response card on reset
  const chatCard = document.getElementById('chat-response-card');
  if (chatCard) chatCard.style.display = 'none';

  showToast('🔄 Scenario reset to Malpe baseline defaults');
  onTideStationChange();
}

function syncScenarioFromForm() {
  const vessel = document.getElementById('inp-vessel').value;
  const timeVal = document.getElementById('inp-time-select').value;
  const rangeVal = document.getElementById('inp-range').value;
  submitChatMessage(`Update scenario: vessel is ${vessel}, departure ${timeVal}, range ${rangeVal} km`);
}

function onChatInputChange() {
  // If user starts typing their own query, clear active demo pill highlight
  document.querySelectorAll('.journey-pill').forEach(p => p.classList.remove('active'));
}

// ─── REGIONAL SPEECH RECOGNITION (STEP 1 & 2 VOICE INPUT) ─────────────────────
const SPEECH_LANG_MAP = {
  en: 'en-IN',
  kn: 'kn-IN',
  hi: 'hi-IN',
  ta: 'ta-IN',
  te: 'te-IN',
  ml: 'ml-IN',
  mr: 'mr-IN',
  gu: 'gu-IN',
  bn: 'bn-IN',
  or: 'or-IN',
  pa: 'pa-IN'
};

const LANG_NAMES = {
  en: 'English',
  kn: 'Kannada (ಕನ್ನಡ)',
  hi: 'Hindi (हिन्दी)',
  ta: 'Tamil (தமிழ்)',
  te: 'Telugu (తెలుగు)',
  ml: 'Malayalam (മലയാളം)',
  mr: 'Marathi (मराठी)',
  gu: 'Gujarati (ગુજરાતી)',
  bn: 'Bengali (বাংলা)',
  or: 'Odia (ଓଡ଼ିଆ)',
  pa: 'Punjabi (ਪੰਜਾਬੀ)'
};

let activeRecognition = null;
let isRecordingVoice = false;
let mediaRecorder = null;
let audioChunks = [];

function toggleVoiceRecording() {
  if (isRecordingVoice) {
    stopVoiceRecording();
  } else {
    startVoiceRecording();
  }
}

async function startVoiceRecording() {
  const micBtn = document.getElementById('btn-mic');
  const micIcon = document.getElementById('mic-icon');
  const inputEl = document.getElementById('chat-input');
  const langKey = currentLanguage || 'en';
  const langTag = SPEECH_LANG_MAP[langKey] || 'en-IN';
  const langDisplay = LANG_NAMES[langKey] || 'English';

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    try {
      activeRecognition = new SpeechRecognition();
      activeRecognition.lang = langTag;
      activeRecognition.continuous = false;
      activeRecognition.interimResults = true;

      const initialText = inputEl ? inputEl.value.trim() : '';
      let speechResultText = '';

      activeRecognition.onstart = () => {
        isRecordingVoice = true;
        if (micBtn) {
          micBtn.classList.add('listening');
          micBtn.title = `Listening in ${langDisplay}... Click to stop`;
        }
        if (micIcon) micIcon.textContent = '🔴';
        showToast(`🎙️ Listening in ${langDisplay}... Speak your query naturally.`);
      };

      activeRecognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        speechResultText = transcript;
        if (inputEl) {
          inputEl.value = initialText ? `${initialText} ${transcript}` : transcript;
        }
      };

      activeRecognition.onerror = (event) => {
        console.warn('Speech recognition event:', event.error);
        stopVoiceRecording();
        if (event.error === 'not-allowed') {
          showToast('⚠️ Microphone permission was denied. Please allow microphone access in browser settings.', 5000);
        } else if (event.error === 'no-speech') {
          showToast('⚠️ No speech detected. Please speak clearly into the microphone.');
        } else {
          showToast(`⚠️ Voice input notice: ${event.error}. You can also type your query.`);
        }
      };

      activeRecognition.onend = () => {
        stopVoiceRecording();
        if (speechResultText.trim()) {
          showToast(`✅ Captured in ${langDisplay}. Click "Analyze Query" or press Enter to submit.`);
        }
      };

      activeRecognition.start();
    } catch (err) {
      console.error('Speech recognition start failed, using fallback:', err);
      startFallbackAudioRecording();
    }
  } else {
    // Fallback using MediaRecorder -> /api/orca/stt (Sarvam AI STT backend)
    startFallbackAudioRecording();
  }
}

function stopVoiceRecording() {
  isRecordingVoice = false;
  const micBtn = document.getElementById('btn-mic');
  const micIcon = document.getElementById('mic-icon');
  if (micBtn) {
    micBtn.classList.remove('listening');
    micBtn.classList.remove('processing');
    micBtn.title = '🎙️ Speak in Indian Regional Language (Kannada, Hindi, Tamil, Telugu, English...)';
  }
  if (micIcon) micIcon.textContent = '🎙️';

  if (activeRecognition) {
    try { activeRecognition.stop(); } catch (e) {}
    activeRecognition = null;
  }
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    try { mediaRecorder.stop(); } catch (e) {}
  }
}

async function startFallbackAudioRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast('⚠️ Microphone recording is not supported in this browser. Please type your query.', 5000);
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    const micBtn = document.getElementById('btn-mic');
    const micIcon = document.getElementById('mic-icon');
    const inputEl = document.getElementById('chat-input');

    mediaRecorder.onstart = () => {
      isRecordingVoice = true;
      if (micBtn) {
        micBtn.classList.add('listening');
        micBtn.title = 'Recording audio... Click to finish';
      }
      if (micIcon) micIcon.textContent = '🔴';
      showToast('🎙️ Recording voice... Speak clearly, then click microphone again to finish.');
    };

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      if (micBtn) {
        micBtn.classList.remove('listening');
        micBtn.classList.add('processing');
      }
      if (micIcon) micIcon.textContent = '⏳';
      showToast('⏳ Transcribing regional voice via Sarvam AI STT...');

      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');

      try {
        const resp = await fetch(`${API}/api/orca/stt`, {
          method: 'POST',
          body: formData
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        const text = data.original_query || data.english_query || '';
        if (text && inputEl) {
          inputEl.value = text;
          showToast('✅ Voice transcribed successfully!');
        }
      } catch (err) {
        showToast(`⚠️ Voice STT notice: ${err.message}. You can also type directly.`);
      } finally {
        stopVoiceRecording();
      }
    };

    mediaRecorder.start();
  } catch (err) {
    stopVoiceRecording();
    showToast(`⚠️ Microphone access error: ${err.message}`);
  }
}

// ─── CONVERSATIONAL ORCA AGENT (P0 & P1) ──────────────────────────────────────
async function submitChatMessage(customText) {
  const inputEl = document.getElementById('chat-input');
  const query = (customText || (inputEl ? inputEl.value : '')).trim();
  if (!query) return;

  // Keep query in the input box so the user can easily view or edit it!
  if (inputEl) {
    inputEl.value = query;
  }
  showToast(`💬 Asking ORCA: "${query.slice(0, 45)}..."`, 4000);

  // Show loading indicator on live response card
  const chatCard = document.getElementById('chat-response-card');
  const chatEcho = document.getElementById('chat-query-echo');
  const chatBody = document.getElementById('chat-response-text');
  const chatPill = document.getElementById('chat-verdict-pill');
  const intentPill = document.getElementById('chat-intent-pill');

  if (chatCard) {
    chatCard.style.display = 'block';
    if (chatEcho) chatEcho.textContent = `"${query}"`;
    if (chatBody) chatBody.innerHTML = '<em>⚡ ORCA Agent is synthesizing real-time INCOIS, MOSDAC & IMD datasets…</em>';
    if (chatPill) {
      chatPill.textContent = 'ANALYZING…';
      chatPill.className = 'chat-verdict-pill reassess';
    }
  }

  animatePipeline(null, 300);

  const btn = document.getElementById('btn-chat-send');
  if (btn) btn.disabled = true;

  try {
    const lang = currentLanguage || 'en';
    const data = await apiFetch('/api/orca/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        session_id: activeSessionId,
        language_override: lang,
        execute_pipeline: true
      })
    });

    renderUnderstandingChips(data.understanding_chips);

    if (data.active_context) {
      const ctx = data.active_context;
      if (ctx.lat) document.getElementById('inp-lat').value = ctx.lat;
      if (ctx.lon) document.getElementById('inp-lon').value = ctx.lon;
      if (ctx.vessel_type) document.getElementById('inp-vessel').value = ctx.vessel_type;
      if (ctx.range_km) document.getElementById('inp-range').value = ctx.range_km;
      if (ctx.station) document.getElementById('inp-station').value = ctx.station;
    }

    const res = data.pipeline_result;
    if (res) {
      if (res.decision_package) renderDecisionPackage(res.decision_package);
      if (res.cartography) renderCartography(res.cartography);
      if (res.evidence_trail) renderEvidence(res.evidence_trail.evidence_trail || []);
      if (res.multilingual_advisory) renderMultilingualAdvisory(res.multilingual_advisory);

      if (res.candidate_pfz_count !== undefined) {
        setMetric('mc-pfz-val', `${res.safe_ranked_pfzs?.length || 0} Safe / ${res.candidate_pfz_count}`);
      }

      // Update Live Conversational Hero Card
      const verdict = res.decision_package?.verdict || 'AVOID';
      const verdictCls = verdict === 'GO' ? 'go' : (verdict === 'AVOID' ? 'avoid' : 'reassess');
      
      const intentTitles = {
        safe_fishing_advisory: '🎯 Safe Fishing Advisory',
        nearest_pfz: '🐟 Nearest Useful PFZ',
        sea_conditions: '🌊 Sea Conditions & Waves',
        productive_safe_zones: '🛡️ Productive & Safe Zones',
        safest_route: '🗺️ Safest Route & Course'
      };

      if (chatPill) {
        chatPill.textContent = verdict;
        chatPill.className = `chat-verdict-pill ${verdictCls}`;
      }
      if (intentPill) {
        intentPill.textContent = intentTitles[data.intent] || '🎯 Marine Advisory';
      }

      const adv = res.multilingual_advisory;
      const responseText = adv?.regional || adv?.english || res.decision_package?.why || 'Analysis completed.';
      
      if (chatBody) {
        chatBody.innerHTML = `
          <div style="font-weight:600;margin-bottom:6px;color:#f8fafc;">${responseText}</div>
          ${adv?.english && adv?.regional && adv.english !== adv.regional ? `<div style="font-size:11.5px;color:#94a3b8;border-top:1px solid rgba(255,255,255,0.06);margin-top:6px;padding-top:6px;">${adv.english}</div>` : ''}
        `;
      }

      const lat = res.context?.location?.lat || parseFloat(document.getElementById('inp-lat').value) || 13.35;
      const lon = res.context?.location?.lon || parseFloat(document.getElementById('inp-lon').value) || 74.70;
      const station = document.getElementById('inp-station').value || 'Malpe';
      
      loadSatellite(lat, lon);
      loadWeather(lat, lon);
      loadTideChart(station);
      loadSVA(res.context?.vessel_profile ? 'motorized_craft' : 'motorized_craft', null, null);
      loadErddap(lat, lon);
    }

    showToast('✅ ORCA Agent Analysis Complete');
  } catch (err) {
    if (chatBody) chatBody.innerHTML = `<span style="color:#ef4444;">⚠️ Analysis failed: ${err.message}</span>`;
    if (chatPill) {
      chatPill.textContent = 'ERROR';
      chatPill.className = 'chat-verdict-pill avoid';
    }
    showToast(`⚠️ Error: ${err.message}`, 5000);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ─── 5 MANDATORY MVP DEMO JOURNEYS (Specification Page 4) ──────────────────────
function triggerDemoJourney(journeyId) {
  const currentStation = document.getElementById('inp-station')?.value || 'Malpe';
  const journeys = {
    1: `I have a 5 m boat. Can I safely go fishing tomorrow morning from ${currentStation}?`,
    2: `Where is the nearest useful PFZ from ${currentStation}?`,
    3: `What are the sea conditions near me in ${currentStation}?`,
    4: `Find a productive area near ${currentStation} that is safe and not restricted.`,
    5: `Show the safest route from ${currentStation} to the selected fishing zone while avoiding restricted areas.`
  };

  const query = journeys[journeyId];
  if (query) {
    // 1. Highlight clicked journey pill
    document.querySelectorAll('.journey-pill').forEach((btn, idx) => {
      if (idx + 1 === journeyId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // 2. Put text directly into input box and keep focus
    const inputEl = document.getElementById('chat-input');
    if (inputEl) {
      inputEl.value = query;
      inputEl.focus();
    }

    // 3. Submit query
    submitChatMessage(query);
  }
}

function renderMultilingualAdvisory(adv) {
  const el = document.getElementById('advisory-content');
  if (!el || !adv) return;

  el.innerHTML = `
    <div class="advisory-block">
      <h3>🌐 ${t('card_advisory_title')} (${adv.language_name?.toUpperCase() || 'REGIONAL'})</h3>
      <div class="advisory-text" style="font-size:13.5px;line-height:1.6;color:#e2e8f0;white-space:pre-line;">
        ${adv.regional || 'Advisory text generated.'}
      </div>
    </div>
    <div class="advisory-block" style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.08);padding-top:10px;">
      <h3 style="color:#94a3b8;font-size:12px;">🇬🇧 English Canonical Advisory</h3>
      <div class="advisory-text" style="font-size:12px;color:#94a3b8;white-space:pre-line;">
        ${adv.english || ''}
      </div>
    </div>
  `;
}

// ─── MARITIME LIMITS (load on startup) ─────────────────────────────────────────
async function loadMaritimeLimits() {
  const el = document.getElementById('maritime-content');
  try {
    const data = await apiFetch('/api/maritime/limits');
    let html = '';
    for (const z of data.maritime_zones) {
      html += `<div class="zone-item">
        <div class="zone-dot" style="background:${z.color_hex}"></div>
        <div class="zone-name">${z.zone}</div>
        <div class="zone-nm">${z.limit_nm} NM</div>
      </div>`;
    }
    html += `<div style="margin-top:10px;font-size:10px;color:var(--c-muted);font-weight:700;letter-spacing:0.8px;text-transform:uppercase;">${t('leg_danger')}</div>`;
    for (const a of data.restricted_areas) {
      html += `<div class="mpa-item">🚫 ${a.name}</div>`;
    }
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = `<div style="color:var(--c-muted);font-size:11px;">Could not load maritime limits</div>`;
  }
}

// ─── SVA Panel ──────────────────────────────────────────────────────────────────
async function loadSVA(vesselType, waveMOverride, windOverride) {
  const el = document.getElementById('sva-content');
  if (!el) return;
  try {
    const wave = waveMOverride || 1.5;
    const wind = windOverride || 28;
    const data = await apiFetch(`/api/vessel/sva/all?wave_m=${wave}&wind_kmh=${wind}`);
    const target = data.advisories.find(a => a.vessel_class.toLowerCase().includes(
      vesselType === 'artisanal_canoe' ? 'canoe' : (vesselType === 'mechanized_trawler' ? 'trawler' : 'motorized')
    )) || data.advisories[1];

    const isSafe = target.is_safe;
    const badgeClass = isSafe ? 'safe' : 'danger';
    const icon = isSafe ? t('sva_clear_to_sail') : t('sva_do_not_sail');

    let html = `<div class="sva-badge ${badgeClass}">${icon}</div>
    <div style="font-size:11px;color:var(--c-muted);margin-bottom:10px;">${target.vessel_class}</div>
    <div class="sva-limits">
      <div class="sva-limit-item">
        <div class="sva-limit-val">${target.sva_limits.max_wave_m} m</div>
        <div class="sva-limit-key">${t('sva_max_wave')}</div>
      </div>
      <div class="sva-limit-item">
        <div class="sva-limit-val">${target.sva_limits.max_wind_kmh} km/h</div>
        <div class="sva-limit-key">${t('sva_max_wind')}</div>
      </div>
      <div class="sva-limit-item">
        <div class="sva-limit-val">${target.sva_limits.max_distance_nm} NM</div>
        <div class="sva-limit-key">${t('sva_max_dist')}</div>
      </div>
      <div class="sva-limit-item">
        <div class="sva-limit-val">Bf ${target.sva_limits.max_beaufort_scale}</div>
        <div class="sva-limit-key">${t('sva_max_beaufort')}</div>
      </div>
    </div>`;

    const violations = target.violations.filter(Boolean);
    if (violations.length) {
      html += `<div class="warning-banner red" style="margin-top:10px;font-size:11px;">⚠️ ${violations.join(' · ')}</div>`;
    }
    html += `<div style="font-size:9px;color:var(--c-muted);margin-top:8px;">Authority: INCOIS / IMD SVA Matrix</div>`;

    el.innerHTML = html;
    setMetric('mc-wave-val', `${wave} m`);
  } catch (e) {
    el.innerHTML = `<div class="warning-banner amber">⚠️ SVA data unavailable</div>`;
  }
}

// ─── Satellite Composite ────────────────────────────────────────────────────────
async function loadSatellite(lat, lon) {
  const el = document.getElementById('satellite-content');
  if (!el) return;
  try {
    const data = await apiFetch(`/api/satellite/composite?lat=${lat}&lon=${lon}`);
    const sst = data.products.sea_surface_temperature;
    const chla = data.products.chlorophyll_a;
    const front = data.products.thermal_front;
    const wind = data.products.surface_wind_scatterometry;
    const sla = data.products.sea_level_anomaly;

    setMetric('mc-sst-val', `${sst.value} °C`);
    setMetric('mc-chla-val', `${chla.value} mg/m³`);

    const fishClass = chla.fishing_productivity === 'HIGH' ? 'high' : (chla.fishing_productivity === 'MODERATE' ? 'mod' : 'low');

    el.innerHTML = `<div class="sat-platform">📡 ${data.satellite_platform} · Last overpass: ${data.last_overpass}</div>
    <div class="sat-grid">
      <div class="sat-item">
        <div class="sat-key">${t('metric_sst')}</div>
        <div class="sat-val">${sst.value} °C</div>
        <div class="sat-flag ok">Δ ${sst.anomaly_from_climatology > 0 ? '+' : ''}${sst.anomaly_from_climatology}°C</div>
      </div>
      <div class="sat-item">
        <div class="sat-key">${t('metric_chla')}</div>
        <div class="sat-val">${chla.value} mg/m³</div>
        <div class="sat-flag ${fishClass}">${t('sat_fish_prod')}: ${chla.fishing_productivity}</div>
      </div>
      <div class="sat-item">
        <div class="sat-key">Wind (SCAT-3)</div>
        <div class="sat-val">${wind.value_kmh} km/h</div>
        <div class="sat-flag ok">Dir: ${wind.direction_deg}°</div>
      </div>
      <div class="sat-item">
        <div class="sat-key">Sea Level Anomaly</div>
        <div class="sat-val">${sla.value_cm > 0 ? '+' : ''}${sla.value_cm} cm</div>
        <div class="sat-flag ok">${sla.unit}</div>
      </div>
    </div>
    <div class="thermal-badge ${front.detected ? 'active' : 'none'}">
      ${front.detected ? '🔥 THERMAL FRONT DETECTED' : '○ No Thermal Front'} · PFZ Probability: ${front.pfz_probability}
    </div>`;
  } catch (e) {
    el.innerHTML = `<div class="warning-banner amber">⚠️ Satellite data unavailable</div>`;
  }
}

// ─── Tide Chart ─────────────────────────────────────────────────────────────────
async function loadTideChart(station) {
  try {
    const data = await apiFetch(`/api/tide/predict?station=${encodeURIComponent(station)}&hours=24`);
    const forecast = data.hourly_forecast;
    const heights = forecast.map(f => f.tide_height_m);
    const labels = forecast.filter((_, i) => i % 3 === 0).map(f => `+${f.hours_from_now}h`);

    renderTideChart(heights, labels);

    const hi = data.next_high_tide;
    const lo = data.next_low_tide;
    const dep = data.optimal_departure_window;

    let metaHtml = '';
    if (hi) metaHtml += `<span class="hi">▲ High Tide +${hi.hours_from_now}h (${hi.tide_height_m}m)</span>`;
    if (lo) metaHtml += `<span class="lo">▼ Low Tide +${lo.hours_from_now}h (${lo.tide_height_m}m)</span>`;
    metaHtml += `<span>Range: ${data.tidal_range_m}m · Station: <strong>${data.station}</strong></span>`;
    document.getElementById('tide-meta').innerHTML = metaHtml;

    if (dep && dep.recommended_departure_hours_from_now !== undefined) {
      document.getElementById('tide-meta').innerHTML +=
        `<div class="tide-depart">⚓ Optimal departure: +${dep.recommended_departure_hours_from_now}h · Return: +${dep.recommended_return_hours_from_now}h (${data.station})</div>`;
    }

    setMetric('mc-tide-val', hi ? `HIGH +${hi.hours_from_now}h` : 'MID');
  } catch (e) {
    const meta = document.getElementById('tide-meta');
    if (meta) meta.textContent = 'Tide data unavailable for station';
  }
}

function renderTideChart(heights, labels) {
  const canvas = document.getElementById('tide-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.offsetWidth || 400;
  const H = 140;
  canvas.width = W;
  canvas.height = H;

  const pad = { t: 12, b: 24, l: 30, r: 10 };
  const drawW = W - pad.l - pad.r;
  const drawH = H - pad.t - pad.b;

  const min = Math.min(...heights) - 0.15;
  const max = Math.max(...heights) + 0.15;
  const range = max - min;

  const xScale = i => pad.l + (i / (heights.length - 1)) * drawW;
  const yScale = v => pad.t + (1 - (v - min) / range) * drawH;

  ctx.clearRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.05)';
  ctx.lineWidth = 1;
  for (let y = 0; y <= 4; y++) {
    const yy = pad.t + (y / 4) * drawH;
    ctx.beginPath(); ctx.moveTo(pad.l, yy); ctx.lineTo(W - pad.r, yy); ctx.stroke();
  }

  // Gradient fill
  const grad = ctx.createLinearGradient(0, pad.t, 0, H - pad.b);
  grad.addColorStop(0, 'rgba(0, 163, 255, 0.35)');
  grad.addColorStop(1, 'rgba(0, 163, 255, 0.0)');

  ctx.beginPath();
  ctx.moveTo(xScale(0), yScale(heights[0]));
  for (let i = 1; i < heights.length; i++) {
    const x0 = xScale(i - 1), y0 = yScale(heights[i - 1]);
    const x1 = xScale(i),     y1 = yScale(heights[i]);
    const cpx = (x0 + x1) / 2;
    ctx.bezierCurveTo(cpx, y0, cpx, y1, x1, y1);
  }
  ctx.lineTo(xScale(heights.length - 1), H - pad.b);
  ctx.lineTo(xScale(0), H - pad.b);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Line
  ctx.beginPath();
  ctx.moveTo(xScale(0), yScale(heights[0]));
  for (let i = 1; i < heights.length; i++) {
    const x0 = xScale(i - 1), y0 = yScale(heights[i - 1]);
    const x1 = xScale(i),     y1 = yScale(heights[i]);
    const cpx = (x0 + x1) / 2;
    ctx.bezierCurveTo(cpx, y0, cpx, y1, x1, y1);
  }
  ctx.strokeStyle = '#00a3ff';
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // Labels
  ctx.fillStyle = 'rgba(100,116,139,0.9)';
  ctx.font = '9px Inter, sans-serif';
  ctx.textAlign = 'center';
  const step = Math.floor(heights.length / 8);
  for (let i = 0; i < heights.length; i += step) {
    ctx.fillText(`+${i}h`, xScale(i), H - 4);
  }
}

// ─── Weather / Cyclone / Warning ────────────────────────────────────────────────
async function loadWeather(lat, lon) {
  const el = document.getElementById('weather-content');
  if (!el) return;
  try {
    const data = await apiFetch(`/api/weather/marine/${lat}/${lon}`);
    const c = data.current || {};
    const imd = await apiFetch(`/api/imd/warning?lat=${lat}&lon=${lon}`).catch(() => ({}));
    const cyclones = await apiFetch('/api/imd/cyclones').catch(() => ({ cyclones: [] }));

    const tempC = c.temperature ?? '--';
    const windKmh = c.wind_speed_kmh ?? '--';
    const waveM = c.wave_height_m ?? data.wave_height_m ?? '--';
    const vis = c.visibility_km ?? '--';
    const humid = c.humidity_pct ?? '--';
    const beaufort = c.beaufort_scale ?? '--';

    if (typeof waveM === 'number') setMetric('mc-wave-val', `${waveM} m`);

    let html = `<div class="weather-grid">
      <div class="wx-item"><div class="wx-val">${tempC}°C</div><div class="wx-key">Temperature</div></div>
      <div class="wx-item"><div class="wx-val">${windKmh} km/h</div><div class="wx-key">Wind Speed</div></div>
      <div class="wx-item"><div class="wx-val">${typeof waveM === 'number' ? waveM + ' m' : waveM}</div><div class="wx-key">Wave Ht (Hs)</div></div>
      <div class="wx-item"><div class="wx-val">${vis} km</div><div class="wx-key">Visibility</div></div>
      <div class="wx-item"><div class="wx-val">${humid}%</div><div class="wx-key">Humidity</div></div>
      <div class="wx-item"><div class="wx-val">Bf ${beaufort}</div><div class="wx-key">Beaufort Scale</div></div>
    </div>`;

    if (imd.warning_level) {
      const wClass = imd.warning_level === 'NONE' ? 'green' : (imd.warning_level === 'CAUTION' ? 'amber' : 'red');
      html += `<div class="warning-banner ${wClass}">⚡ ${imd.warning_text || imd.warning_level}</div>`;
    }

    if (cyclones.cyclones && cyclones.cyclones.length > 0) {
      html += `<div class="warning-banner red">🌀 CYCLONE ALERT: ${cyclones.cyclones[0].name || 'Active System'}</div>`;
    } else {
      html += `<div class="warning-banner green">${t('cyclone_no_active')}</div>`;
    }

    html += `<div style="font-size:10px;color:var(--c-muted);margin-top:6px;">⚡ ${t('lightning_risk')}: ${data.lightning_risk ?? 'LOW'} · Source: IMD Radar Network</div>`;
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = `<div class="warning-banner amber">⚠️ Weather data unavailable — ${e.message}</div>`;
  }
}

// ─── ERDDAP Dataset ─────────────────────────────────────────────────────────────
async function loadErddap(lat, lon) {
  const el = document.getElementById('erddap-content');
  if (!el) return;
  try {
    const data = await apiFetch(`/api/erddap/dataset?lat=${lat}&lon=${lon}`);
    let vars = data.variables.map(v => `<span class="erddap-var">${v.name}</span>`).join('');
    let fmts = data.data_format_options.map(f => `<span class="fmt-badge">${f}</span>`).join('');
    el.innerHTML = `
      <div class="erddap-meta">
        <strong style="color:var(--c-text)">Dataset:</strong> ${data.dataset_id}<br/>
        <strong style="color:var(--c-text)">Protocol:</strong> ${data.access_protocol} | <strong>Authority:</strong> INCOIS
      </div>
      <div style="margin-top:8px;font-size:10px;color:var(--c-muted);text-transform:uppercase;letter-spacing:0.8px;font-weight:700;">Variables</div>
      <div class="erddap-vars">${vars}</div>
      <div style="margin-top:8px;font-size:10px;color:var(--c-muted);text-transform:uppercase;letter-spacing:0.8px;font-weight:700;">Output Formats</div>
      <div class="erddap-formats">${fmts}</div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="warning-banner amber">⚠️ ERDDAP data unavailable</div>`;
  }
}

// ─── Evidence Trail ─────────────────────────────────────────────────────────────
function renderEvidence(trail) {
  const el = document.getElementById('evidence-content');
  if (!el) return;
  if (!trail?.length) {
    el.innerHTML = '<div style="color:var(--c-muted);font-size:11px">Run analysis to view live provenance audit</div>';
    return;
  }
  el.innerHTML = trail.slice(0, 8).map(ev => `
    <div class="evidence-item">
      <div class="ev-param">${ev.data_point || ev.parameter || 'Parameter'}</div>
      <div class="ev-val">${ev.status || 'VERIFIED'}</div>
      <div class="ev-src">${ev.source} · ${ev.timestamp}</div>
      ${ev.verified ? `<span class="ev-quality good">QC: PASSED</span>` : ''}
    </div>
  `).join('');
}

// ─── Metric helper ──────────────────────────────────────────────────────────────
function setMetric(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ─── MAIN: Run Full Analysis ────────────────────────────────────────────────────
async function runFullAnalysis() {
  const station = document.getElementById('inp-station')?.value || 'Malpe';
  const stationData = TIDE_STATIONS_REGISTRY[station] || TIDE_STATIONS_REGISTRY['Malpe'];
  
  const lat = parseFloat(document.getElementById('inp-lat').value) || stationData.lat;
  const lon = parseFloat(document.getElementById('inp-lon').value) || stationData.lon;
  const vessel = document.getElementById('inp-vessel').value;
  const lang = currentLanguage || 'en';
  const timeVal = document.getElementById('inp-time-select')?.value || 'Tomorrow 05:00 AM';
  const rangeVal = parseFloat(document.getElementById('inp-range')?.value) || 35.0;

  // Sync understanding chips with form inputs
  const chipLoc = document.getElementById('chip-val-loc');
  if (chipLoc) chipLoc.textContent = `${stationData.name} (${lat}°N, ${lon}°E)`;
  
  const vesselSel = document.getElementById('inp-vessel');
  const vesselText = vesselSel?.options[vesselSel.selectedIndex]?.text || vessel;
  const chipVessel = document.getElementById('chip-val-vessel');
  if (chipVessel) chipVessel.textContent = vesselText;

  const chipTime = document.getElementById('chip-val-time');
  if (chipTime) chipTime.textContent = timeVal;

  const chipRange = document.getElementById('chip-val-range');
  if (chipRange) chipRange.textContent = `${rangeVal} km`;

  const btn = document.getElementById('btn-analyze');
  if (btn) {
    btn.disabled = true;
    btn.textContent = '⟳ Analysing…';
  }

  showToast(`🌊 Executing ORCA 10-step decision loop for ${stationData.label}…`, 4000);
  animatePipeline(null, 250);

  try {
    const data = await apiFetch(`/api/orca/query?lat=${lat}&lon=${lon}&vessel=${vessel}&language=${lang}&departure_time=${encodeURIComponent(timeVal)}&max_range_km=${rangeVal}`);
    
    if (data.decision_package) renderDecisionPackage(data.decision_package);
    if (data.cartography) renderCartography(data.cartography);
    if (data.evidence_trail) renderEvidence(data.evidence_trail.evidence_trail || []);
    if (data.multilingual_advisory) renderMultilingualAdvisory(data.multilingual_advisory);

    if (data.candidate_pfz_count !== undefined) {
      setMetric('mc-pfz-val', `${data.safe_ranked_pfzs?.length || 0} Safe / ${data.candidate_pfz_count}`);
    }

    // Refresh satellite, tide, weather, and SVA in parallel for the selected station
    await Promise.allSettled([
      loadSatellite(lat, lon),
      loadTideChart(station),
      loadWeather(lat, lon),
      loadSVA(vessel, null, null),
      loadErddap(lat, lon),
    ]);

    showToast(`✅ ORCA Analysis Complete for ${stationData.name}!`);
  } catch (err) {
    showToast(`⚠️ Analysis error: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = `⚓ ${t('btn_run_decision_loop')}`;
    }
  }
}

// ─── Auto-load on Page Startup ────────────────────────────────────────────────
(async function init() {
  // Load stored language if available
  try {
    const savedLang = localStorage.getItem('orca_language');
    if (savedLang && I18N_TRANSLATIONS[savedLang]) {
      currentLanguage = savedLang;
      const langSel = document.getElementById('lang-select');
      if (langSel) langSel.value = savedLang;
    }
  } catch (e) {}

  applyLanguage(currentLanguage);
  initOperationalMap();
  loadMaritimeLimits();
  onTideStationChange();
})();
