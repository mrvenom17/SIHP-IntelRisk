import React from 'react';
import { motion } from 'framer-motion';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  animate?: boolean;
}

const GlassCard: React.FC<GlassCardProps> = ({ children, className = '', animate = false }) => {
  const cardClass = `bg-gray-900/20 backdrop-blur-lg border border-gray-700/30 rounded-xl p-6 ${className}`;

  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={cardClass}
      >
        {children}
      </motion.div>
    );
  }

  return <div className={cardClass}>{children}</div>;
};

export default GlassCard;