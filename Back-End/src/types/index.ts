export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'analyst' | 'viewer';
  created_at: Date;
  updated_at: Date;
}

export interface RawReport {
  id: string;
  source: string;
  content: string;
  url?: string;
  timestamp: Date;
  location?: {
    latitude: number;
    longitude: number;
  };
  metadata: Record<string, any>;
}

export interface VerifiedReport {
  id: string;
  raw_report_id: string;
  verified: boolean;
  confidence_score: number;
  verification_notes: string;
  verified_by: string;
  verified_at: Date;
}

export interface HumanHotspot {
  id: string;
  title: string;
  description: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  event_type: 'earthquake' | 'flood' | 'fire' | 'storm' | 'other';
  created_by: string;
  created_at: Date;
}

export interface DisasterHotspot {
  id: string;
  title: string;
  description: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  event_type: 'earthquake' | 'flood' | 'fire' | 'storm' | 'other';
  confidence: number;
  sources: number;
  detected_at: Date;
}

export interface CompositeHotspot {
  id: string;
  title: string;
  description: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  panic_score: number;
  event_type: 'earthquake' | 'flood' | 'fire' | 'storm' | 'other';
  confidence: number;
  sources: number;
  emotions: {
    panic: number;
    fear: number;
    anger: number;
    sadness: number;
  };
  contributing_reports: string[];
  created_at: Date;
  updated_at: Date;
}

export interface FactCheckRequest {
  id: string;
  content: string;
  url?: string;
  user_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: {
    is_factual: boolean;
    confidence: number;
    explanation: string;
    sources: string[];
  };
  created_at: Date;
  completed_at?: Date;
}

export interface AuthRequest extends Request {
  user?: User;
}