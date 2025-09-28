import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    if (error.response?.status === 401) {
      console.log('Unauthorized - clearing auth data');
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      // Don't reload immediately, let the auth context handle it
      setTimeout(() => window.location.reload(), 100);
    }
    return Promise.reject(error);
  }
);

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  role?: 'admin' | 'analyst' | 'viewer';
}

export interface FactCheckRequest {
  content: string;
  url?: string;
}

export interface HotspotFilters {
  timeRange?: string;
  severity?: string;
  eventType?: string;
  minConfidence?: number;
  limit?: number;
  offset?: number;
}

// Auth API
export const authAPI = {
  login: async (credentials: LoginCredentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterData) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout: async () => {
    try {
      const response = await api.post('/auth/logout');
      return response.data;
    } catch (error) {
      // Silent fail for logout
      return null;
    }
  },
};

// Hotspots API
export const hotspotsAPI = {
  getCompositeHotspots: async (filters: HotspotFilters = {}) => {
    try {
    const response = await api.get('/hotspots/composite', { params: filters });
    return response.data;
    } catch (error) {
      console.error('Failed to fetch from API, falling back to mock data');
      // Fallback to mock data
      const mockResponse = await fetch('/src/data/mockHotspots.json');
      if (mockResponse.ok) {
        return await mockResponse.json();
      }
      // If mock data also fails, return empty
      return { hotspots: [] };
    }
  },

  getHotspotById: async (id: string) => {
    const response = await api.get(`/hotspots/composite/${id}`);
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/hotspots/stats');
    return response.data;
  },

  createHumanHotspot: async (hotspot: any) => {
    const response = await api.post('/hotspots/human', hotspot);
    return response.data;
  },
};

// Fact Check API
export const factCheckAPI = {
  submitFactCheck: async (request: FactCheckRequest) => {
    const response = await api.post('/fact-check', request);
    return response.data;
  },

  getFactCheckResult: async (id: string) => {
    const response = await api.get(`/fact-check/${id}`);
    return response.data;
  },

  getFactCheckHistory: async (limit?: number) => {
    const response = await api.get('/fact-check', { params: { limit } });
    return response.data;
  },
};

// Export API
export const exportAPI = {
  exportJSON: async (filters: HotspotFilters = {}) => {
    const response = await api.get('/export/json', { 
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  },

  exportCSV: async (filters: HotspotFilters = {}) => {
    const response = await api.get('/export/csv', { 
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  },
};

export default api;