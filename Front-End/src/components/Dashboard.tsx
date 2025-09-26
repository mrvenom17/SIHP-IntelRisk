import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Menu, Bell, Settings, User, LogOut, BarChart3, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import MapView from './MapView';
import Navigation from './Navigation';
import { useAuth } from '../hooks/useAuth';
import { hotspotsAPI } from '../services/api';
import { Hotspot, FilterState } from '../types';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isNavOpen, setIsNavOpen] = useState(false);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    timeRange: '24h',
    disasterTypes: [],
    severityLevels: [],
    confidenceMin: 0,
    showPanic: true,
    showPhysical: true,
  });

  useEffect(() => {
    fetchHotspots();
  }, [filters.timeRange, filters.confidenceMin]);

  const fetchHotspots = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await hotspotsAPI.getCompositeHotspots({
        timeRange: filters.timeRange,
        minConfidence: filters.confidenceMin,
        limit: 100
      });
      
      setHotspots(response.hotspots || []);
    } catch (error: any) {
      console.error('Error fetching hotspots:', error);
      setError('Failed to load hotspots. Please try again.');
      
      // Fallback to mock data if API fails
      const mockHotspots: Hotspot[] = [
        {
          id: '1',
          latitude: 37.7749,
          longitude: -122.4194,
          severity: 'critical',
          panicScore: 85,
          eventType: 'fire',
          title: 'Wildfire Emergency - California',
          description: 'Large wildfire spreading rapidly through residential areas',
          timestamp: new Date().toISOString(),
          sources: 247,
          confidence: 92,
          emotions: { panic: 85, fear: 78, anger: 23, sadness: 45 }
        },
        {
          id: '2',
          latitude: 35.6762,
          longitude: 139.6503,
          severity: 'high',
          panicScore: 72,
          eventType: 'earthquake',
          title: 'Earthquake Alert - Tokyo',
          description: 'Strong earthquake detected, buildings shaking',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          sources: 156,
          confidence: 88,
          emotions: { panic: 72, fear: 67, anger: 12, sadness: 34 }
        }
      ];
      setHotspots(mockHotspots);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setIsNavOpen(false);
  };

  return (
    <div className="h-screen bg-slate-900 flex flex-col overflow-hidden">
      {/* Header */}
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="bg-gray-900/95 backdrop-blur-lg border-b border-gray-700/30 px-6 py-4 z-30"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => setIsNavOpen(true)}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all mr-4"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-white">SIHP-IntelRisk</h1>
              <p className="text-sm text-gray-400">Disaster Intelligence Platform</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="relative">
              <Bell className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition-colors" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full flex items-center justify-center">
                <span className="text-xs text-white font-bold">{hotspots.filter(h => h.severity === 'critical').length}</span>
              </div>
            </div>
            <button
              onClick={() => handleNavigation('/analytics')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
              title="Analytics"
            >
              <BarChart3 className="w-5 h-5" />
            </button>
            <button
              onClick={() => handleNavigation('/fact-check')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
              title="Fact Checker"
            >
              <Search className="w-5 h-5" />
            </button>
            <Settings className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition-colors" />
            <div className="flex items-center space-x-2">
              <User className="w-5 h-5 text-gray-400" />
              <span className="text-sm text-gray-300">{user?.name || 'User'}</span>
              <span className="text-xs text-teal-400 bg-teal-400/20 px-2 py-1 rounded-full">
                {user?.role || 'viewer'}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <div className="flex-1 relative">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-400 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading disaster intelligence...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-red-400 mb-4">⚠️</div>
              <p className="text-gray-400 mb-4">{error}</p>
              <button
                onClick={fetchHotspots}
                className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <MapView hotspots={hotspots} filters={filters} />
        )}
        
        <Navigation
          isOpen={isNavOpen}
          onClose={() => setIsNavOpen(false)}
          filters={filters}
          onFiltersChange={setFilters}
          onNavigate={handleNavigation}
        />

        {/* Real-time Status Indicator */}
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="bg-green-500/20 border border-green-400 text-green-300 px-4 py-2 rounded-full text-sm flex items-center"
          >
            <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
            Live Monitoring Active • {hotspots.length} Hotspots
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;