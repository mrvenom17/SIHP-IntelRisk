export interface Hotspot {
  id: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  panicScore: number;
  eventType: 'earthquake' | 'flood' | 'fire' | 'storm' | 'other';
  title: string;
  description: string;
  timestamp: string;
  sources: number;
  confidence: number;
  emotions: {
    panic: number;
    fear: number;
    anger: number;
    sadness: number;
  };
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'analyst' | 'viewer';
}

export interface FilterState {
  timeRange: '1h' | '6h' | '24h' | '7d' | '30d';
  disasterTypes: string[];
  severityLevels: string[];
  confidenceMin: number;
  showPanic: boolean;
  showPhysical: boolean;
}