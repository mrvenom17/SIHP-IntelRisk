import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  ExternalLink,
  FileText,
  Loader
} from 'lucide-react';
import GlassCard from './GlassCard';
import { factCheckAPI } from '../services/api';

interface FactCheckResult {
  id: string;
  content: string;
  url?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: {
    is_factual: boolean;
    confidence: number;
    explanation: string;
    sources: string[];
  };
  created_at: string;
  completed_at?: string;
}

const FactChecker: React.FC = () => {
  const [content, setContent] = useState('');
  const [url, setUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentCheck, setCurrentCheck] = useState<FactCheckResult | null>(null);
  const [history, setHistory] = useState<FactCheckResult[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await factCheckAPI.submitFactCheck({
        content: content.trim(),
        url: url.trim() || undefined
      });

      const requestId = response.request_id;
      
      // Poll for results
      pollForResult(requestId);
      
      // Clear form
      setContent('');
      setUrl('');
    } catch (error: any) {
      console.error('Failed to submit fact check:', error);
      alert('Failed to submit fact check request');
    } finally {
      setIsSubmitting(false);
    }
  };

  const pollForResult = async (requestId: string) => {
    const maxAttempts = 30; // 30 seconds max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await factCheckAPI.getFactCheckResult(requestId);
        const result = response.fact_check;
        
        setCurrentCheck(result);
        
        if (result.status === 'completed' || result.status === 'failed') {
          // Add to history
          setHistory(prev => [result, ...prev.slice(0, 9)]); // Keep last 10
          return;
        }
        
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1000);
        }
      } catch (error) {
        console.error('Error polling for result:', error);
      }
    };

    poll();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-400" />;
      case 'processing':
        return <Loader className="w-5 h-5 text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getFactualityIcon = (isFactual: boolean) => {
    return isFactual ? (
      <CheckCircle className="w-6 h-6 text-green-400" />
    ) : (
      <XCircle className="w-6 h-6 text-red-400" />
    );
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-400';
    if (confidence >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="p-6 space-y-6 bg-slate-900 min-h-screen">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">Fact Checker</h1>
        <p className="text-gray-400">Verify news articles and claims using AI-powered analysis</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <GlassCard animate>
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <Search className="w-5 h-5 mr-2 text-teal-400" />
              Submit for Verification
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Content to Verify *
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste the news article, claim, or content you want to fact-check..."
                  className="w-full h-32 px-4 py-3 bg-gray-800/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-400/20 transition-all resize-none"
                  required
                  maxLength={5000}
                />
                <div className="text-xs text-gray-400 mt-1">
                  {content.length}/5000 characters
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Source URL (Optional)
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  className="w-full px-4 py-3 bg-gray-800/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-400/20 transition-all"
                />
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isSubmitting || !content.trim()}
                className="w-full py-3 bg-gradient-to-r from-teal-500 to-cyan-500 text-white font-semibold rounded-lg shadow-lg hover:shadow-teal-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isSubmitting ? (
                  <>
                    <Loader className="w-5 h-5 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    Verify Content
                  </>
                )}
              </motion.button>
            </form>
          </GlassCard>
        </motion.div>

        {/* Current Check Result */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <GlassCard animate>
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
              <FileText className="w-5 h-5 mr-2 text-teal-400" />
              Verification Result
            </h2>

            <AnimatePresence mode="wait">
              {currentCheck ? (
                <motion.div
                  key={currentCheck.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(currentCheck.status)}
                      <span className="ml-2 text-sm text-gray-300 capitalize">
                        {currentCheck.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(currentCheck.created_at).toLocaleString()}
                    </div>
                  </div>

                  <div className="bg-gray-800/30 rounded-lg p-3">
                    <p className="text-sm text-gray-300 line-clamp-3">
                      {currentCheck.content}
                    </p>
                    {currentCheck.url && (
                      <a
                        href={currentCheck.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-xs text-teal-400 hover:text-teal-300 mt-2"
                      >
                        <ExternalLink className="w-3 h-3 mr-1" />
                        Source
                      </a>
                    )}
                  </div>

                  {currentCheck.result && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          {getFactualityIcon(currentCheck.result.is_factual)}
                          <span className="ml-2 text-white font-medium">
                            {currentCheck.result.is_factual ? 'Likely Factual' : 'Potentially False'}
                          </span>
                        </div>
                        <div className={`text-sm font-medium ${getConfidenceColor(currentCheck.result.confidence)}`}>
                          {currentCheck.result.confidence}% confidence
                        </div>
                      </div>

                      <div className="bg-gray-800/30 rounded-lg p-3">
                        <h4 className="text-sm font-medium text-gray-300 mb-2">Analysis</h4>
                        <p className="text-sm text-gray-400">
                          {currentCheck.result.explanation}
                        </p>
                      </div>

                      {currentCheck.result.sources.length > 0 && (
                        <div className="bg-gray-800/30 rounded-lg p-3">
                          <h4 className="text-sm font-medium text-gray-300 mb-2">Sources</h4>
                          <div className="space-y-1">
                            {currentCheck.result.sources.map((source, index) => (
                              <a
                                key={index}
                                href={source}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block text-xs text-teal-400 hover:text-teal-300 truncate"
                              >
                                {source}
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}
                </motion.div>
              ) : (
                <div className="text-center py-8">
                  <AlertTriangle className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400">No verification in progress</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Submit content above to start fact-checking
                  </p>
                </div>
              )}
            </AnimatePresence>
          </GlassCard>
        </motion.div>
      </div>

      {/* History */}
      {history.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <GlassCard animate>
            <h2 className="text-xl font-semibold text-white mb-4">Recent Verifications</h2>
            <div className="space-y-3">
              {history.map((check) => (
                <div
                  key={check.id}
                  className="bg-gray-800/30 rounded-lg p-3 hover:bg-gray-800/50 transition-colors cursor-pointer"
                  onClick={() => setCurrentCheck(check)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      {getStatusIcon(check.status)}
                      {check.result && (
                        <div className="ml-2">
                          {getFactualityIcon(check.result.is_factual)}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(check.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <p className="text-sm text-gray-300 line-clamp-2">
                    {check.content}
                  </p>
                  {check.result && (
                    <div className="mt-2 text-xs text-gray-400">
                      Confidence: {check.result.confidence}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      )}
    </div>
  );
};

export default FactChecker;