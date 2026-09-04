export type AgentState = 'idle' | 'running' | 'conflict' | 'rechecking' | 'validated' | 'degraded';

export type AgentStatus = {
  name: string;
  role: string;
  state: AgentState;
  source: string;
  details?: string;
  latency?: string;
};

export type EvidenceItem = {
  source: string;
  parameter?: string;
  value?: string;
  summary: string;
  confidence?: 'High' | 'Moderate' | 'Cross-Checked' | 'Validated' | 'Degraded';
  timestamp?: string;
};

export type Recommendation = {
  verdict: 'SAFE' | 'CAUTION' | 'HAZARD' | 'ADVISORY';
  headline: string;
  summary: string;
  confidenceScore: string;
  validationState: 'validated' | 'rechecking' | 'conflict' | 'degraded';
  evidence: EvidenceItem[];
};

export type ConversationTurn = {
  id: string;
  role: 'user' | 'sagarvani';
  text: string;
  timestamp?: string;
  recommendation?: Recommendation;
  evidence?: EvidenceItem[];
  intent?: string;
  validationTrace?: string[];
};

export type Readout = {
  label: string;
  value: string;
  unit?: string;
  isActive?: boolean;
  trend?: 'up' | 'down' | 'stable';
};

export type Alert = {
  id: string;
  type: 'danger' | 'warning' | 'info';
  title: string;
  message: string;
  source: string;
  coordinates?: [number, number];
  timestamp: string;
};

export type MapLayer = 
  | 'SST' 
  | 'Currents' 
  | 'PFZ' 
  | 'Cyclone' 
  | 'Wave Height'
  | 'High Wave Warnings'
  | 'Vessel Route';

export type VoiceState = 'idle' | 'listening' | 'processing' | 'transcript' | 'error';

export type LanguageCode = 'en' | 'hi' | 'kn' | 'ta' | 'te' | 'ml' | 'bn' | 'mr' | 'gu';
