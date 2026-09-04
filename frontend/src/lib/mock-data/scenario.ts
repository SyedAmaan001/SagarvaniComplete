import { AgentStatus, ConversationTurn, Readout, Alert, MapLayer } from "../types";

export const initialAgents: AgentStatus[] = [
  { 
    name: 'Marine Data Agent', 
    role: 'Ocean Observations', 
    state: 'idle', 
    source: 'INCOIS Ocean Buoy & Forecast Feeds',
    details: 'Monitors SST, wave spectrum, sea state, and currents.' 
  },
  { 
    name: 'Weather Agent', 
    role: 'Atmospheric Context', 
    state: 'idle', 
    source: 'IMD Coastal Doppler & GFS',
    details: 'Tracks barometric pressure, wind vectors, squall warnings.' 
  },
  { 
    name: 'GIS Agent', 
    role: 'Geospatial Layering', 
    state: 'idle', 
    source: 'ISRO Bhuvan / NRSC / Bhoonidhi',
    details: 'Calculates shoreline distances, EEZ bounds, and navigation paths.' 
  },
  { 
    name: 'Ocean Analytics Agent', 
    role: 'Multi-Sensor Analytics', 
    state: 'idle', 
    source: 'MOSDAC & In-situ Historical Archive',
    details: 'Discovers multi-variable trends, anomalies, and thermal fronts.' 
  },
  { 
    name: 'Risk Agent', 
    role: 'Decision Safety Analysis', 
    state: 'idle', 
    source: 'INCOIS Surge & IMD Cyclone Trackers',
    details: 'Evaluates vessel-specific hazard limits and exposure windows.' 
  },
  { 
    name: 'Spatial Reasoning Agent', 
    role: 'Topological Reasoning', 
    state: 'idle', 
    source: 'ORCA Spatial Knowledge Engine',
    details: 'Evaluates distance buffers, safe return corridors, and harbour depths.' 
  },
];

export const initialReadouts: Readout[] = [
  { label: 'Sea State', value: '2', unit: 'Slight' },
  { label: 'Wind Speed', value: '12', unit: 'knots', trend: 'stable' },
  { label: 'Wave Height', value: '1.2', unit: 'm', isActive: true, trend: 'stable' },
  { label: 'SST Surface', value: '28.4', unit: '°C' },
  { label: 'Active Alerts', value: '0', trend: 'stable' },
];

export interface PredefinedScenario {
  id: string;
  name: string;
  query: string;
  badge: string;
  isContradiction: boolean;
  intent: string;
  runningAgents: string[];
  conflictAgents?: string[];
  recheckingSteps: string[];
  turn: ConversationTurn;
  readouts: Readout[];
  alerts: Alert[];
  layers: MapLayer[];
}

export const PREDEFINED_SCENARIOS: PredefinedScenario[] = [
  {
    id: "safe-fishing-mangalore",
    name: "Safe Fishing Window (Mangalore)",
    query: "Is it safe for an 11-meter boat to fish 15 nautical miles off Mangalore Port tomorrow morning between 05:00 and 12:00?",
    badge: "Routine Advisory",
    isContradiction: false,
    intent: "Pre-departure trip safety evaluation for small craft in coastal Karnataka waters.",
    runningAgents: [
      "Marine Data Agent",
      "Weather Agent",
      "GIS Agent",
      "Risk Agent",
      "Spatial Reasoning Agent",
      "Ocean Analytics Agent"
    ],
    recheckingSteps: [
      "1. ORCA parsed intent: Location [12.91°N, 74.85°E], Window [05:00 - 12:00 IST], Craft [11m Trawler].",
      "2. Weather Agent retrieved IMD coastal forecast: Wind 10–14 kts WSW, clear visibility, 0 squall probability.",
      "3. Marine Data Agent queried INCOIS Buoy #AD04 & Wave Spectrum: Significant Wave Height 1.1m, Peak Period 7.8s.",
      "4. GIS Agent mapped coordinates to 15nm offshore within Karnataka EEZ boundary.",
      "5. Ocean Analytics Agent verified no localized thermal inversion or steep bathymetric swell magnification.",
      "6. Risk Agent checked small vessel hazard threshold (< 1.8m wave height limit): Condition is well within SAFE threshold.",
      "7. Spatial Reasoning Agent plotted safe transit corridor to and from Mangalore Old Port.",
      "8. ORCA Consensus Layer: All 6 agents validate SAFE recommendation with 0 contradictions."
    ],
    turn: {
      id: "turn-safe-1",
      role: "sagarvani",
      timestamp: "10:30 AM IST",
      intent: "Trip Safety & Wave Window Analysis",
      text: "SAFE TO OPERATE. Wave heights off Mangalore are forecasted between 1.0m and 1.3m with gentle winds of 10–14 knots from the West-Southwest. No squall activity or high-swell warnings are active. An optimal 7-hour fishing window exists between 05:00 and 12:00 IST within 18 nautical miles of the coastline.",
      recommendation: {
        verdict: "SAFE",
        headline: "Favorable Marine Conditions for 11m Craft",
        summary: "Wave height (1.1m) and wind conditions (12 kts) remain within safe operating thresholds throughout the requested morning window.",
        confidenceScore: "High (Multi-Source Agreement)",
        validationState: "validated",
        evidence: [
          {
            source: "INCOIS Ocean Wave Forecast",
            parameter: "Significant Wave Height",
            value: "1.1m (Period: 7.8s)",
            summary: "Calm to slight sea state across coastal Karnataka sector.",
            confidence: "High",
            timestamp: "Updated 15 mins ago"
          },
          {
            source: "IMD Coastal Marine Bulletin",
            parameter: "Surface Wind & Visibility",
            value: "10–14 kts WSW, Visibility > 8km",
            summary: "No squalls or pre-monsoon convective cells detected on Mangalore radar.",
            confidence: "High",
            timestamp: "Updated 30 mins ago"
          },
          {
            source: "ISRO Bhuvan Coastal GIS",
            parameter: "Spatial Bathymetry Corridor",
            value: "Safe depth > 24m at 15nm",
            summary: "Clear transit corridor without navigational hazards or shallow shoals.",
            confidence: "Cross-Checked",
            timestamp: "Validated"
          }
        ]
      },
      evidence: [
        {
          source: "INCOIS Ocean Wave Forecast",
          summary: "1.1m wave height at [12.91°N, 74.85°E] during 0500-1200 hrs."
        },
        {
          source: "IMD Marine Radar",
          summary: "Zero convective squall development predicted within 30nm radius."
        },
        {
          source: "ISRO Bhuvan Coastal Elevation",
          summary: "Depth and wave refraction within nominal safety baseline."
        }
      ]
    },
    readouts: [
      { label: 'Sea State', value: '2', unit: 'Slight', trend: 'stable' },
      { label: 'Wind Speed', value: '12', unit: 'knots', trend: 'stable' },
      { label: 'Wave Height', value: '1.1', unit: 'm', isActive: true, trend: 'down' },
      { label: 'SST Surface', value: '28.6', unit: '°C' },
      { label: 'Active Alerts', value: '0', trend: 'stable' },
    ],
    alerts: [],
    layers: ['Wave Height', 'Currents']
  },
  {
    id: "contradiction-squall",
    name: "Contradiction & Re-Planning (Squall vs Calm Wind)",
    query: "Local weather looks calm in Udupi, but radio says rough sea. Is it safe to head 25 nautical miles out for tuna today?",
    badge: "Contradiction Demo",
    isContradiction: true,
    intent: "Resolve conflict between calm shore wind and offshore rough sea warnings.",
    runningAgents: [
      "Marine Data Agent",
      "Weather Agent",
      "GIS Agent",
      "Risk Agent",
      "Spatial Reasoning Agent",
      "Ocean Analytics Agent"
    ],
    conflictAgents: ["Weather Agent", "Marine Data Agent"],
    recheckingSteps: [
      "1. Initial Retrieval: Local coastal weather station reports calm surface winds (7 knots).",
      "2. Divergent Finding: INCOIS offshore wave buoy #AD04 detects rapidly growing 2.8m long-period swell (11.4s period).",
      "3. CONTRADICTION DETECTED: Discrepancy between onshore perceived wind calm and offshore wave energy.",
      "4. ORCA RE-PLANNING TRIGGERED: Re-dispatching Ocean Analytics & Risk Agents with high-resolution MOSDAC satellite altimetry.",
      "5. Re-check Discovery: A distant pre-monsoon squall line 60nm southwest is propagating high swell waves into the Udupi fishing grounds without localized shore wind.",
      "6. Risk Agent Re-assessment: 2.8m swell with 11.4s period poses severe capsizing hazard for vessels under 15m.",
      "7. Spatial Reasoning Agent: Safe return boundary restricted to < 6 nautical miles from coast.",
      "8. Reconciled Advisory: Issue CAUTION advisory explaining the swell mechanism and citing the cross-checked buoy data."
    ],
    turn: {
      id: "turn-conflict-1",
      role: "sagarvani",
      timestamp: "10:32 AM IST",
      intent: "Resolve Wind vs Swell Contradiction & Issue Safety Advisory",
      text: "CAUTION ADVISED — DO NOT PROCEED 25 NM OFFSHORE. Although nearshore surface winds appear calm (6–8 knots), INCOIS wave buoys and MOSDAC satellite altimetry confirm a steep 2.8m long-period swell (11.4s period) propagating from a distant offshore squall line. For craft under 15m, operations should remain restricted within 6 nautical miles of the coastline.",
      recommendation: {
        verdict: "CAUTION",
        headline: "Distant Offshore Swell Hazard Despite Calm Local Wind",
        summary: "Contradiction between shore wind and ocean swell was cross-checked. High swell energy (2.8m) exceeds safe stability limits for small fishing craft beyond 6nm.",
        confidenceScore: "Validated via Re-Checking",
        validationState: "conflict",
        evidence: [
          {
            source: "INCOIS Offshore Buoy #AD04",
            parameter: "Significant Swell Height",
            value: "2.8m (Period: 11.4s)",
            summary: "High energy long-period swell detected moving toward Karnataka shelf.",
            confidence: "Cross-Checked",
            timestamp: "Re-checked live"
          },
          {
            source: "IMD Satellite & Doppler Radar",
            parameter: "Offshore Squall Vector",
            value: "Developing squall 60nm SW",
            summary: "Explains high wave energy despite calm local coastal barometric pressure.",
            confidence: "Validated",
            timestamp: "Re-checked live"
          },
          {
            source: "MOSDAC OceanSat-3 Altimetry",
            parameter: "Sea Surface Roughness",
            value: "High energy wave spectrum",
            summary: "Confirmed swell propagation corridor intersecting the 25nm tuna zone.",
            confidence: "High",
            timestamp: "Validated"
          }
        ]
      },
      evidence: [
        {
          source: "INCOIS Buoy #AD04",
          summary: "2.8m swell height (11.4s period) detected 20nm offshore."
        },
        {
          source: "IMD Squall Bulletin",
          summary: "Offshore convective squall generating swell without shore wind."
        },
        {
          source: "ORCA Re-planning Engine",
          summary: "Resolved contradiction by incorporating satellite altimetry verification."
        }
      ]
    },
    readouts: [
      { label: 'Sea State', value: '4', unit: 'Rough', trend: 'up' },
      { label: 'Wind Speed', value: '8', unit: 'knots (Nearshore)', trend: 'down' },
      { label: 'Wave Height', value: '2.8', unit: 'm (Offshore)', isActive: true, trend: 'up' },
      { label: 'SST Surface', value: '27.9', unit: '°C' },
      { label: 'Active Alerts', value: '2', trend: 'up' },
    ],
    alerts: [
      {
        id: "alert-squall-1",
        type: "danger",
        title: "High Swell Advisory (2.8m)",
        message: "Dangerous long-period swell active beyond 6nm from Udupi to Mangalore.",
        source: "INCOIS + ORCA Re-check",
        coordinates: [13.35, 74.35],
        timestamp: "10:32 AM"
      },
      {
        id: "alert-squall-2",
        type: "warning",
        title: "Distant Squall Propagation",
        message: "Convective cell generating swell 60nm SW of Karnataka coast.",
        source: "IMD Doppler",
        coordinates: [12.5, 73.8],
        timestamp: "10:30 AM"
      }
    ],
    layers: ['Wave Height', 'Cyclone', 'High Wave Warnings']
  },
  {
    id: "pfz-advisory",
    name: "Potential Fishing Zone (PFZ) & Thermal Front",
    query: "Show me Potential Fishing Zone (PFZ) coordinates and ocean current vectors near Karwar for pelagic catch today.",
    badge: "PFZ & GIS",
    isContradiction: false,
    intent: "Locate Potential Fishing Zones derived from SST fronts and Chlorophyll-a satellite data.",
    runningAgents: [
      "Marine Data Agent",
      "GIS Agent",
      "Ocean Analytics Agent",
      "Spatial Reasoning Agent"
    ],
    recheckingSteps: [
      "1. ORCA parsed intent: Potential Fishing Zone advisory for Karwar sector [14.81°N, 74.12°E].",
      "2. Marine Data Agent retrieved INCOIS PFZ advisory & MODIS Chlorophyll-a concentration (0.45 mg/m³).",
      "3. Ocean Analytics Agent extracted SST thermal gradient: 28.2°C shelf boundary meeting 27.4°C upwelling tongue.",
      "4. GIS Agent overlaid PFZ polygon with 20–40m depth bathymetric contours.",
      "5. Spatial Reasoning Agent computed optimal bearing: 245° SW from Karwar fishing harbour (14.2 nm).",
      "6. Risk Agent validated sea state: Wave height 1.2m, completely safe for multi-day pelagic operations.",
      "7. ORCA Consensus Layer: Validated advisory with exact coordinates and navigation vector."
    ],
    turn: {
      id: "turn-pfz-1",
      role: "sagarvani",
      timestamp: "10:35 AM IST",
      intent: "Potential Fishing Zone & Thermal Front Mapping",
      text: "PFZ ADVISORY IDENTIFIED. A prominent oceanographic front is active 14.2 nautical miles Southwest of Karwar harbour (Bearing 245°). Satellite SST indicators reveal a 0.8°C thermal gradient accompanied by elevated Chlorophyll-a (0.45 mg/m³), indicating high pelagic fish aggregation (mackerel/sardine). Sea state is favorable with 1.2m waves and 12 knots NW wind.",
      recommendation: {
        verdict: "ADVISORY",
        headline: "Active PFZ Front 14.2nm SW of Karwar",
        summary: "Co-located thermal boundary and chlorophyll bloom detected. Favorable navigation and sea conditions.",
        confidenceScore: "High (Satellite Corroborated)",
        validationState: "validated",
        evidence: [
          {
            source: "INCOIS PFZ Advisory Service",
            parameter: "PFZ Polygon Coordinates",
            value: "14.65°N - 14.72°N, 73.92°E - 74.05°E",
            summary: "Ocean color front matching historical pelagic shoaling patterns.",
            confidence: "High",
            timestamp: "Daily Ingestion"
          },
          {
            source: "ISRO OceanSat-3 / Bhoonidhi",
            parameter: "Chlorophyll-a & SST Front",
            value: "0.45 mg/m³, 27.4°C / 28.2°C",
            summary: "Sharp boundary layer confirming active coastal upwelling.",
            confidence: "High",
            timestamp: "Morning Pass"
          },
          {
            source: "INCOIS Surface Currents",
            parameter: "Current Vector",
            value: "0.8 knots South-Southeast",
            summary: "Stable drift pattern aiding net deployment.",
            confidence: "High",
            timestamp: "Real-time"
          }
        ]
      },
      evidence: [
        {
          source: "INCOIS PFZ Advisory",
          summary: "Confirmed pelagic zone at 14.68°N, 73.98°E (14.2nm from Karwar)."
        },
        {
          source: "ISRO OceanSat-3",
          summary: "SST thermal boundary cross-validated with Chlorophyll bloom."
        }
      ]
    },
    readouts: [
      { label: 'Sea State', value: '2', unit: 'Slight', trend: 'stable' },
      { label: 'Wind Speed', value: '12', unit: 'knots NW', trend: 'stable' },
      { label: 'Wave Height', value: '1.2', unit: 'm', isActive: true, trend: 'stable' },
      { label: 'SST Surface', value: '27.4', unit: '°C (Front)', trend: 'down' },
      { label: 'Active Alerts', value: '0', trend: 'stable' },
    ],
    alerts: [],
    layers: ['PFZ', 'SST', 'Currents']
  }
];
