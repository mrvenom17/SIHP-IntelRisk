import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, AlertTriangle, Info } from 'lucide-react';
import ParticleBackground from './ParticleBackground';
import GlassCard from './GlassCard';
import { useAuth } from '../hooks/useAuth';

interface LoginProps {
  switchToRegister: () => void;
}

const Login: React.FC<LoginProps> = ({ switchToRegister }) => {
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: 'ace@gmail.com',
    password: 'pass',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      await login(formData.email, formData.password);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fillTestCredentials = () => {
    setFormData({
      email: 'ace@gmail.com',
      password: 'pass'
    });
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center relative overflow-hidden">
      <ParticleBackground />
      
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10"
      >
        <GlassCard className="w-96 max-w-md">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <AlertTriangle className="w-8 h-8 text-teal-400 mr-2" />
              <h1 className="text-2xl font-bold text-white">SIHP-IntelRisk</h1>
            </div>
            <p className="text-gray-400">Disaster Intelligence Platform</p>
          </div>

          {/* Test Credentials Info */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-teal-500/10 border border-teal-400/30 rounded-lg p-3 mb-6"
          >
            <div className="flex items-start">
              <Info className="w-4 h-4 text-teal-400 mr-2 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="text-teal-300 font-medium mb-1">Test Credentials</p>
                <p className="text-teal-200/80 text-xs">
                  Email: ace@gmail.com<br />
                  Password: pass
                </p>
                <button
                  type="button"
                  onClick={fillTestCredentials}
                  className="text-teal-400 hover:text-teal-300 text-xs underline mt-1"
                >
                  Click to fill automatically
                </button>
              </div>
            </div>
          </motion.div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <motion.input
                  whileFocus={{ scale: 1.02 }}
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full pl-11 pr-4 py-3 bg-gray-800/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-400/20 transition-all"
                  placeholder="Enter your email"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <motion.input
                  whileFocus={{ scale: 1.02 }}
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full pl-11 pr-11 py-3 bg-gray-800/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-400/20 transition-all"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-500/20 border border-red-400 text-red-300 px-4 py-3 rounded-lg text-sm"
              >
                {error}
              </motion.div>
            )}

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-gradient-to-r from-teal-500 to-cyan-500 text-white font-semibold rounded-lg shadow-lg hover:shadow-teal-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden"
            >
              {isLoading && (
                <div className="absolute inset-0 bg-white/10 animate-pulse" />
              )}
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </motion.button>

            <div className="text-center">
              <p className="text-gray-400 text-sm">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={switchToRegister}
                  className="text-teal-400 hover:text-teal-300 font-medium transition-colors"
                >
                  Create Account
                </button>
              </p>
            </div>
          </form>
        </GlassCard>
      </motion.div>
    </div>
  );
};

export default Login;