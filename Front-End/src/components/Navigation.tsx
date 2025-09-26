import React from 'react';
import { motion } from 'framer-motion';
import { 
  Map, 
  BarChart3, 
  Search,
  Download, 
  Filter,
  Clock,
  AlertTriangle,
  TrendingUp
} from 'lucide-react';
import { FilterState } from '../types';

interface NavigationProps {
  isOpen: boolean;
  onClose: () => void;
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onNavigate: (path: string) => void;
}

const Navigation: React.FC<NavigationProps> = ({ isOpen, onClose, filters, onFiltersChange, onNavigate }) => {
  return (
    <>
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          onClick={onClose}
        />
      )}
      
      <motion.div
        initial={{ x: -400 }}
        animate={{ x: isOpen ? 0 : -400 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="fixed left-0 top-0 h-full w-80 bg-gray-900/90 backdrop-blur-lg border-r border-gray-700/30 z-50 p-6"
      >
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-semibold text-white">Controls</h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="space-y-6">
          {/* Navigation Links */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-300 mb-3">
              <Map className="w-4 h-4 mr-2" />
              Navigation
            </label>
            <div className="space-y-2">
              <button
                onClick={() => onNavigate('/dashboard')}
                className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
              >
                Dashboard
              </button>
              <button
                onClick={() => onNavigate('/analytics')}
                className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
              >
                Analytics
              </button>
              <button
                onClick={() => onNavigate('/fact-check')}
                className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
              >
                Fact Checker
              </button>
            </div>
          </div>

          {/* Time Range Filter */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-300 mb-3">
              <Clock className="w-4 h-4 mr-2" />
              Time Range
            </label>
            <div className="grid grid-cols-3 gap-2">
              {['1h', '6h', '24h', '7d', '30d'].map((range) => (
                <button
                  key={range}
                  onClick={() => onFiltersChange({ ...filters, timeRange: range as any })}
                  className={`px-3 py-2 text-xs rounded-lg border transition-all ${
                    filters.timeRange === range
                      ? 'bg-teal-500/20 border-teal-400 text-teal-300'
                      : 'bg-gray-800/50 border-gray-600 text-gray-400 hover:border-gray-500'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>

          {/* Disaster Types */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-300 mb-3">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Disaster Types
            </label>
            <div className="space-y-2">
              {['earthquake', 'flood', 'fire', 'storm', 'other'].map((type) => (
                <label key={type} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.disasterTypes.includes(type)}
                    onChange={(e) => {
                      const newTypes = e.target.checked
                        ? [...filters.disasterTypes, type]
                        : filters.disasterTypes.filter(t => t !== type);
                      onFiltersChange({ ...filters, disasterTypes: newTypes });
                    }}
                    className="mr-3 accent-teal-500"
                  />
                  <span className="text-sm text-gray-300 capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Severity Levels */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-300 mb-3">
              <TrendingUp className="w-4 h-4 mr-2" />
              Severity Levels
            </label>
            <div className="space-y-2">
              {['low', 'medium', 'high', 'critical'].map((level) => (
                <label key={level} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.severityLevels.includes(level)}
                    onChange={(e) => {
                      const newLevels = e.target.checked
                        ? [...filters.severityLevels, level]
                        : filters.severityLevels.filter(l => l !== level);
                      onFiltersChange({ ...filters, severityLevels: newLevels });
                    }}
                    className="mr-3 accent-amber-500"
                  />
                  <span className="text-sm text-gray-300 capitalize">{level}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Confidence Threshold */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-300 mb-3">
              <Filter className="w-4 h-4 mr-2" />
              Min Confidence: {filters.confidenceMin}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={filters.confidenceMin}
              onChange={(e) => onFiltersChange({ ...filters, confidenceMin: parseInt(e.target.value) })}
              className="w-full accent-teal-500"
            />
          </div>

          {/* Display Options */}
          <div>
            <label className="flex items-center text-sm font-medium text-gray-300 mb-3">
              <Map className="w-4 h-4 mr-2" />
              Display Options
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.showPanic}
                  onChange={(e) => onFiltersChange({ ...filters, showPanic: e.target.checked })}
                  className="mr-3 accent-red-500"
                />
                <span className="text-sm text-gray-300">Show Panic Overlays</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.showPhysical}
                  onChange={(e) => onFiltersChange({ ...filters, showPhysical: e.target.checked })}
                  className="mr-3 accent-orange-500"
                />
                <span className="text-sm text-gray-300">Show Physical Severity</span>
              </label>
            </div>
          </div>
        </div>

        {/* Export Options */}
        <div className="absolute bottom-6 left-6 right-6">
          <div className="space-y-2">
            <button className="w-full px-4 py-2 bg-teal-600/20 border border-teal-500 text-teal-300 rounded-lg hover:bg-teal-600/30 transition-colors flex items-center justify-center">
              <Download className="w-4 h-4 mr-2" />
              Export JSON
            </button>
            <button className="w-full px-4 py-2 bg-amber-600/20 border border-amber-500 text-amber-300 rounded-lg hover:bg-amber-600/30 transition-colors flex items-center justify-center">
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </button>
          </div>
        </div>
      </motion.div>
    </>
  );
};

export default Navigation;