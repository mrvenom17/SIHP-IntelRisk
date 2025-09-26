import React from 'react';
import { motion } from 'framer-motion';
import { Hotspot } from '../types';
import { Clock, Users, TrendingUp, AlertTriangle } from 'lucide-react';

interface HotspotTooltipProps {
  hotspot: Hotspot;
  position: { x: number; y: number };
}

const HotspotTooltip: React.FC<HotspotTooltipProps> = ({ hotspot, position }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/20 border-red-500';
      case 'high': return 'text-orange-400 bg-orange-500/20 border-orange-500';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500';
      case 'low': return 'text-green-400 bg-green-500/20 border-green-500';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-500';
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

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.8, y: 10 }}
      transition={{ duration: 0.2 }}
      className="absolute z-50 w-80 bg-gray-900/95 backdrop-blur-lg border border-gray-700/50 rounded-xl p-4 shadow-2xl"
      style={{
        left: position.x,
        top: position.y - 20,
        transform: 'translate(-50%, -100%)'
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center">
          <span className="text-2xl mr-2">{getEventIcon(hotspot.eventType)}</span>
          <div>
            <h3 className="text-white font-semibold text-sm">{hotspot.title}</h3>
            <p className="text-gray-400 text-xs capitalize">{hotspot.eventType}</p>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs rounded-lg border ${getSeverityColor(hotspot.severity)}`}>
          {hotspot.severity.toUpperCase()}
        </span>
      </div>

      <p className="text-gray-300 text-sm mb-4">{hotspot.description}</p>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="flex items-center text-xs">
          <TrendingUp className="w-3 h-3 mr-1 text-red-400" />
          <span className="text-gray-400">Panic Score:</span>
          <span className="text-red-400 ml-1 font-medium">{hotspot.panicScore}</span>
        </div>
        <div className="flex items-center text-xs">
          <Users className="w-3 h-3 mr-1 text-teal-400" />
          <span className="text-gray-400">Sources:</span>
          <span className="text-teal-400 ml-1 font-medium">{hotspot.sources}</span>
        </div>
        <div className="flex items-center text-xs">
          <AlertTriangle className="w-3 h-3 mr-1 text-amber-400" />
          <span className="text-gray-400">Confidence:</span>
          <span className="text-amber-400 ml-1 font-medium">{hotspot.confidence}%</span>
        </div>
        <div className="flex items-center text-xs">
          <Clock className="w-3 h-3 mr-1 text-blue-400" />
          <span className="text-gray-400">
            {new Date(hotspot.timestamp).toLocaleTimeString()}
          </span>
        </div>
      </div>

      <div className="border-t border-gray-700 pt-3">
        <h4 className="text-gray-300 text-xs font-medium mb-2">Emotional Analysis</h4>
        <div className="space-y-1">
          {Object.entries(hotspot.emotions).map(([emotion, value]) => (
            <div key={emotion} className="flex items-center justify-between text-xs">
              <span className="text-gray-400 capitalize">{emotion}</span>
              <div className="flex items-center">
                <div className="w-12 h-1 bg-gray-700 rounded-full mr-2">
                  <div 
                    className={`h-full rounded-full ${
                      emotion === 'panic' ? 'bg-red-400' :
                      emotion === 'fear' ? 'bg-orange-400' :
                      emotion === 'anger' ? 'bg-red-600' : 'bg-blue-400'
                    }`}
                    style={{ width: `${value}%` }}
                  />
                </div>
                <span className="text-gray-300 w-6 text-right">{value}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default HotspotTooltip;