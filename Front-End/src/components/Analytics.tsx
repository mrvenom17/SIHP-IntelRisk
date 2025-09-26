import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from 'recharts';
import { TrendingUp, AlertTriangle, Activity, Clock } from 'lucide-react';
import GlassCard from './GlassCard';

const Analytics: React.FC = () => {
  const navigate = useNavigate();

  const timeSeriesData = [
    { time: '00:00', panic: 65, severity: 45, reports: 120 },
    { time: '04:00', panic: 45, severity: 30, reports: 80 },
    { time: '08:00', panic: 78, severity: 62, reports: 200 },
    { time: '12:00', panic: 92, severity: 85, reports: 340 },
    { time: '16:00', panic: 88, severity: 78, reports: 280 },
    { time: '20:00', panic: 72, severity: 58, reports: 190 },
  ];

  const severityDistribution = [
    { name: 'Critical', value: 15, color: '#DC2626' },
    { name: 'High', value: 28, color: '#EA580C' },
    { name: 'Medium', value: 42, color: '#D97706' },
    { name: 'Low', value: 35, color: '#059669' },
  ];

  const emotionHeatmapData = [
    { emotion: 'Panic', value: 85, color: '#DC2626' },
    { emotion: 'Fear', value: 72, color: '#EA580C' },
    { emotion: 'Anger', value: 45, color: '#F59E0B' },
    { emotion: 'Sadness', value: 38, color: '#3B82F6' },
  ];

  const regionData = [
    { region: 'North America', incidents: 45, avgSeverity: 68 },
    { region: 'Europe', incidents: 32, avgSeverity: 55 },
    { region: 'Asia Pacific', incidents: 78, avgSeverity: 82 },
    { region: 'South America', incidents: 23, avgSeverity: 49 },
    { region: 'Africa', incidents: 34, avgSeverity: 71 },
  ];

  return (
    <div className="p-6 space-y-6 bg-slate-900 min-h-screen">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center text-gray-400 hover:text-white mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </button>
        <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
        <p className="text-gray-400">Real-time disaster intelligence insights</p>
      </motion.div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: 'Active Hotspots', value: '247', change: '+12%', icon: AlertTriangle, color: 'text-red-400' },
          { title: 'Avg Panic Score', value: '76', change: '+8%', icon: TrendingUp, color: 'text-orange-400' },
          { title: 'Reports/Hour', value: '1,234', change: '+23%', icon: Activity, color: 'text-teal-400' },
          { title: 'Response Time', value: '4.2s', change: '-15%', icon: Clock, color: 'text-blue-400' },
        ].map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <GlassCard className="p-4" animate>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">{metric.title}</p>
                  <p className="text-2xl font-bold text-white mt-1">{metric.value}</p>
                  <p className={`text-sm mt-1 ${metric.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                    {metric.change} from last hour
                  </p>
                </div>
                <metric.icon className={`w-8 h-8 ${metric.color}`} />
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <GlassCard animate>
            <h3 className="text-lg font-semibold text-white mb-4">Panic & Severity Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="panic"
                  stroke="#DC2626"
                  strokeWidth={2}
                  dot={{ fill: '#DC2626', strokeWidth: 2, r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="severity"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </GlassCard>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <GlassCard animate>
            <h3 className="text-lg font-semibold text-white mb-4">Severity Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {severityDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </GlassCard>
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <GlassCard animate>
            <h3 className="text-lg font-semibold text-white mb-4">Emotional Analysis</h3>
            <div className="space-y-4">
              {emotionHeatmapData.map((emotion, index) => (
                <div key={emotion.emotion} className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm font-medium">{emotion.emotion}</span>
                  <div className="flex items-center space-x-3">
                    <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${emotion.value}%` }}
                        transition={{ delay: 0.5 + index * 0.1, duration: 1 }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: emotion.color }}
                      />
                    </div>
                    <span className="text-white text-sm font-medium w-8 text-right">
                      {emotion.value}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <GlassCard animate>
            <h3 className="text-lg font-semibold text-white mb-4">Regional Incidents</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={regionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="region" 
                  stroke="#9CA3AF" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Bar 
                  dataKey="incidents" 
                  fill="#14B8A6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        </motion.div>
      </div>

      {/* Reports Timeline */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <GlassCard animate>
          <h3 className="text-lg font-semibold text-white mb-4">Reports Volume</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Area
                type="monotone"
                dataKey="reports"
                stroke="#14B8A6"
                fill="url(#colorReports)"
                strokeWidth={2}
              />
              <defs>
                <linearGradient id="colorReports" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14B8A6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#14B8A6" stopOpacity={0} />
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </GlassCard>
      </motion.div>
    </div>
  );
};

export default Analytics;