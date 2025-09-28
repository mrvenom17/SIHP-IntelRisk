import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Hotspot, FilterState } from '../types';
import HotspotTooltip from './HotspotTooltip';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapViewProps {
  hotspots: Hotspot[];
  filters: FilterState;
}

// Custom marker icons for different severity levels
const createCustomIcon = (severity: string, eventType: string) => {
  const colors = {
    critical: '#DC2626',
    high: '#EA580C',
    medium: '#D97706',
    low: '#059669'
  };

  const color = colors[severity as keyof typeof colors] || '#6B7280';
  
  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        color: white;
        font-weight: bold;
      ">
        ${getEventIcon(eventType)}
      </div>
    `,
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
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

// Component to handle map updates
const MapUpdater: React.FC<{ hotspots: Hotspot[] }> = ({ hotspots }) => {
  const map = useMap();

  useEffect(() => {
    if (hotspots.length > 0) {
      const group = new L.FeatureGroup(
        hotspots.map(hotspot => 
          L.marker([hotspot.latitude, hotspot.longitude])
        )
      );
      map.fitBounds(group.getBounds().pad(0.1));
    }
  }, [hotspots, map]);

  return null;
};

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

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapUpdater hotspots={filteredHotspots} />
        
        {filteredHotspots.map((hotspot) => (
          <Marker
            key={hotspot.id}
            position={[hotspot.latitude, hotspot.longitude]}
            icon={createCustomIcon(hotspot.severity, hotspot.eventType)}
          >
            <Popup>
              <div className="p-2 min-w-[250px]">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-800">{hotspot.title}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    hotspot.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    hotspot.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                    hotspot.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {hotspot.severity.toUpperCase()}
                  </span>
                </div>
                
                <p className="text-gray-600 text-sm mb-3">{hotspot.description}</p>
                
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="font-medium">Panic Score:</span>
                    <span className="ml-1 text-red-600">{hotspot.panicScore}</span>
                  </div>
                  <div>
                    <span className="font-medium">Sources:</span>
                    <span className="ml-1 text-blue-600">{hotspot.sources}</span>
                  </div>
                  <div>
                    <span className="font-medium">Confidence:</span>
                    <span className="ml-1 text-green-600">{hotspot.confidence}%</span>
                  </div>
                  <div>
                    <span className="font-medium">Time:</span>
                    <span className="ml-1 text-gray-600">
                      {new Date(hotspot.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                
                <div className="mt-3 pt-2 border-t border-gray-200">
                  <h4 className="font-medium text-xs text-gray-700 mb-1">Emotions</h4>
                  <div className="space-y-1">
                    {Object.entries(hotspot.emotions).map(([emotion, value]) => (
                      <div key={emotion} className="flex items-center justify-between text-xs">
                        <span className="capitalize text-gray-600">{emotion}</span>
                        <div className="flex items-center">
                          <div className="w-8 h-1 bg-gray-200 rounded-full mr-1">
                            <div 
                              className={`h-full rounded-full ${
                                emotion === 'panic' ? 'bg-red-400' :
                                emotion === 'fear' ? 'bg-orange-400' :
                                emotion === 'anger' ? 'bg-red-600' : 'bg-blue-400'
                              }`}
                              style={{ width: `${value}%` }}
                            />
                          </div>
                          <span className="text-gray-700 w-6 text-right">{value}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

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