import express from 'express';
import cors from 'cors';
import path from 'path';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import { initializeDatabase } from './config/database';

// Import routes
import authRoutes from './routes/auth';
import hotspotsRoutes from './routes/hotspots';
import factCheckRoutes from './routes/factCheck';
import exportRoutes from './routes/export';

dotenv.config();

console.log('🚀 Starting SIHP-IntelRisk Backend Server...');
console.log('Environment:', process.env.NODE_ENV || 'development');

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000'), // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100'),
  message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'SIHP-IntelRisk Backend API',
    version: '1.0.0',
    endpoints: ['/api/v1/auth', '/api/v1/hotspots', '/api/v1/fact-check', '/api/v1/export']
  });
});

// API routes
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/hotspots', hotspotsRoutes);
app.use('/api/v1/fact-check', factCheckRoutes);
app.use('/api/v1/export', exportRoutes);

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Unhandled error:', err);
  console.error('Stack:', err.stack);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Initialize database and start server
const startServer = async () => {
  try {
    console.log('🔧 Initializing database...');
    await initializeDatabase();
    
    app.listen(PORT, () => {
      console.log(`🚀 SIHP-IntelRisk Backend running on port ${PORT}`);
      console.log(`📊 Health check: http://localhost:${PORT}/health`);
      console.log(`🔗 API Base URL: http://localhost:${PORT}/api/v1`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    console.error('Error details:', error);
    process.exit(1);
  }
};

startServer();

export default app;