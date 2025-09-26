import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Hotspot, FilterState } from '../types';
import HotspotTooltip from './HotspotTooltip';

interface MapViewProps {
  hotspots: Hotspot[];
  filters: FilterState;
}

const MapView: React.FC<MapViewProps> = ({ hotspots, filters }) => {
  const [hoveredHotspot, setHoveredHotspot] = useState<Hotspot | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const filteredHotspots = hotspots.filter(hotspot => {
    if (filters.disasterTypes.length > 0 && !filters.disasterTypes.includes(hotspot.eventType)) {
      return false;
    }
    if (filters.severityLevels.length > 0 && !filters.severityLevels.includes(hotspot.severity)) {
      return false;
    }
    if (hotspot.confidence < filters.confidenceMin) {
      return false;
    }
    return true;
  });

  const handleMouseMove = (event: React.MouseEvent) => {
    setMousePosition({ x: event.clientX, y: event.clientY });
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#DC2626';
      case 'high': return '#EA580C';
      case 'medium': return '#D97706';
      case 'low': return '#059669';
      default: return '#6B7280';
    }
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'earthquake': return '🌍';
      case 'flood': return '🌊';
      case 'fire': return '🔥';
      case 'storm': return '⛈️';
      default: return '⚠️';
    }
  };

  // Convert lat/lng to screen coordinates (simplified projection)
  const projectToScreen = (lat: number, lng: number, width: number, height: number) => {
    const x = ((lng + 180) / 360) * width;
    const y = ((90 - lat) / 180) * height;
    return { x, y };
  };

  return (
    <div className="relative h-full w-full bg-slate-900 overflow-hidden" onMouseMove={handleMouseMove}>
      {/* World Map Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Grid overlay for map-like appearance */}
        <div className="absolute inset-0 opacity-10">
          <svg width="100%" height="100%">
            <defs>
              <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#14B8A6" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>
        
        {/* Continent outlines (simplified) */}
        <div className="absolute inset-0 opacity-20">
          <svg width="100%" height="100%" viewBox="0 0 1000 500">
            {/* Simplified continent shapes */}
            <path d="M150,200 Q200,180 250,200 Q300,220 350,200 Q400,180 450,200 L450,300 Q400,320 350,300 Q300,280 250,300 Q200,320 150,300 Z" 
                  fill="none" stroke="#14B8A6" strokeWidth="1"/>
            <path d="M500,150 Q550,130 600,150 Q650,170 700,150 Q750,130 800,150 L800,250 Q750,270 700,250 Q650,230 600,250 Q550,270 500,250 Z" 
                  fill="none" stroke="#14B8A6" strokeWidth="1"/>
          </svg>
        </div>
      </div>

      {/* Hotspot Markers */}
      <div className="absolute inset-0">
        {filteredHotspots.map((hotspot) => {
          const screenPos = projectToScreen(
            hotspot.latitude, 
            hotspot.longitude, 
            window.innerWidth, 
            window.innerHeight
          );
          
          const size = hotspot.severity === 'critical' ? 40 : 
                      hotspot.severity === 'high' ? 32 : 
                      hotspot.severity === 'medium' ? 24 : 16;
          
          const color = getSeverityColor(hotspot.severity);
          
          return (
            <motion.div
              key={hotspot.id}
              className="absolute cursor-pointer"
              style={{
                left: screenPos.x - size / 2,
                top: screenPos.y - size / 2,
              }}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: Math.random() * 0.5 }}
              onMouseEnter={() => setHoveredHotspot(hotspot)}
              onMouseLeave={() => setHoveredHotspot(null)}
            >
              {/* Pulsing background */}
              <motion.div
                className="absolute inset-0 rounded-full"
                style={{ backgroundColor: color }}
                animate={{ 
                  scale: [1, 1.5, 1],
                  opacity: [0.3, 0.1, 0.3]
                }}
                transition={{ 
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
              
              {/* Main marker */}
              <motion.div
                className="relative rounded-full border-2 border-white shadow-lg flex items-center justify-center text-white font-bold"
                style={{ 
                  width: size,
                  height: size,
                  backgroundColor: color,
                  boxShadow: `0 0 20px ${color}60`
                }}
                whileHover={{ scale: 1.2 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <span className="text-xs">
                  {getEventIcon(hotspot.eventType)}
                </span>
              </motion.div>
            </motion.div>
          );
        })}
      </div>

      <AnimatePresence>
        {hoveredHotspot && (
          <HotspotTooltip
            hotspot={hoveredHotspot}
            position={mousePosition}
          />
        )}
      </AnimatePresence>

      {/* Map Layer Controls */}
      <div className="absolute top-4 right-4 z-10 space-y-2">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`px-4 py-2 rounded-lg backdrop-blur-lg border transition-all ${
            filters.showPanic 
              ? 'bg-red-500/20 border-red-400 text-red-300' 
              : 'bg-gray-900/50 border-gray-600 text-gray-400 hover:border-gray-500'
          }`}
        >
          Panic Overlay
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`px-4 py-2 rounded-lg backdrop-blur-lg border transition-all ${
            filters.showPhysical 
              ? 'bg-orange-500/20 border-orange-400 text-orange-300' 
              : 'bg-gray-900/50 border-gray-600 text-gray-400 hover:border-gray-500'
          }`}
        >
          Physical Severity
        </motion.button>
      </div>

      {/* Stats Overlay */}
      <div className="absolute bottom-4 left-4 bg-gray-900/80 backdrop-blur-lg border border-gray-700/30 rounded-lg p-4">
        <div className="flex items-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
            <span className="text-gray-300">Critical: {filteredHotspots.filter(h => h.severity === 'critical').length}</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-orange-500 rounded-full mr-2"></div>
            <span className="text-gray-300">High: {filteredHotspots.filter(h => h.severity === 'high').length}</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
            <span className="text-gray-300">Medium: {filteredHotspots.filter(h => h.severity === 'medium').length}</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span className="text-gray-300">Low: {filteredHotspots.filter(h => h.severity === 'low').length}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;