import { Pool } from 'pg';
import bcrypt from 'bcryptjs';
import dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:password@localhost:5432/sihp_intelrisk',
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

export { pool };

export const initializeDatabase = async () => {
  try {
    // Test PostgreSQL connection
    const client = await pool.connect();
    console.log('✅ Connected to PostgreSQL');
    client.release();
    
    // Create tables if they don't exist
    await createTables();
    
    // Create test user
    await createTestUser();
  } catch (error) {
    console.error('❌ Database initialization error:', error);
    process.exit(1);
  }
};

const createTables = async () => {
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');
    
    // Users table
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(255) NOT NULL,
        role VARCHAR(50) DEFAULT 'viewer' CHECK (role IN ('admin', 'analyst', 'viewer')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Raw reports table
    await client.query(`
      CREATE TABLE IF NOT EXISTS raw_reports (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        source VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        url TEXT,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Verified reports table
    await client.query(`
      CREATE TABLE IF NOT EXISTS verified_reports (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        raw_report_id UUID REFERENCES raw_reports(id),
        verified BOOLEAN NOT NULL,
        confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 100),
        verification_notes TEXT,
        verified_by UUID REFERENCES users(id),
        verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Human hotspots table
    await client.query(`
      CREATE TABLE IF NOT EXISTS human_hotspots (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title VARCHAR(255) NOT NULL,
        description TEXT,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        severity VARCHAR(50) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
        event_type VARCHAR(50) CHECK (event_type IN ('earthquake', 'flood', 'fire', 'storm', 'other')),
        created_by UUID REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Disaster hotspots table
    await client.query(`
      CREATE TABLE IF NOT EXISTS disaster_hotspots (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title VARCHAR(255) NOT NULL,
        description TEXT,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        severity VARCHAR(50) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
        event_type VARCHAR(50) CHECK (event_type IN ('earthquake', 'flood', 'fire', 'storm', 'other')),
        confidence FLOAT CHECK (confidence >= 0 AND confidence <= 100),
        sources INTEGER DEFAULT 0,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Composite hotspots table
    await client.query(`
      CREATE TABLE IF NOT EXISTS composite_hotspots (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title VARCHAR(255) NOT NULL,
        description TEXT,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        severity VARCHAR(50) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
        panic_score FLOAT CHECK (panic_score >= 0 AND panic_score <= 100),
        event_type VARCHAR(50) CHECK (event_type IN ('earthquake', 'flood', 'fire', 'storm', 'other')),
        confidence FLOAT CHECK (confidence >= 0 AND confidence <= 100),
        sources INTEGER DEFAULT 0,
        emotions JSONB DEFAULT '{"panic": 0, "fear": 0, "anger": 0, "sadness": 0}',
        contributing_reports JSONB DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Fact check requests table
    await client.query(`
      CREATE TABLE IF NOT EXISTS fact_check_requests (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        content TEXT NOT NULL,
        url TEXT,
        user_id UUID REFERENCES users(id),
        status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
        result JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
      )
    `);
    
    // Create indexes for better performance
    await client.query('CREATE INDEX IF NOT EXISTS idx_composite_hotspots_location ON composite_hotspots (latitude, longitude)');
    await client.query('CREATE INDEX IF NOT EXISTS idx_composite_hotspots_severity ON composite_hotspots (severity)');
    await client.query('CREATE INDEX IF NOT EXISTS idx_composite_hotspots_created_at ON composite_hotspots (created_at)');
    await client.query('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)');
    await client.query('CREATE INDEX IF NOT EXISTS idx_fact_check_user_id ON fact_check_requests (user_id)');
    
    await client.query('COMMIT');
    console.log('✅ Database tables created successfully');
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
};

const createTestUser = async () => {
  const client = await pool.connect();
  
  try {
    // Check if test user already exists
    const existingUser = await client.query('SELECT id FROM users WHERE email = $1', ['ace@gmail.com']);
    
    if (existingUser.rows.length === 0) {
      // Create test user
      const passwordHash = await bcrypt.hash('pass', 12);
      
      await client.query(
        `INSERT INTO users (email, password_hash, name, role) 
         VALUES ($1, $2, $3, $4)`,
        ['ace@gmail.com', passwordHash, 'Test User', 'admin']
      );
      
      console.log('✅ Test user created: ace@gmail.com / pass');
    } else {
      console.log('✅ Test user already exists: ace@gmail.com / pass');
    }
    
    // Create some sample composite hotspots for demo
    const sampleHotspots = [
      {
        title: 'Wildfire Emergency - California',
        description: 'Large wildfire spreading rapidly through residential areas in Northern California',
        latitude: 37.7749,
        longitude: -122.4194,
        severity: 'critical',
        panic_score: 85,
        event_type: 'fire',
        confidence: 92,
        sources: 247,
        emotions: JSON.stringify({ panic: 85, fear: 78, anger: 23, sadness: 45 })
      },
      {
        title: 'Earthquake Alert - Tokyo',
        description: 'Strong earthquake detected, buildings shaking in downtown Tokyo',
        latitude: 35.6762,
        longitude: 139.6503,
        severity: 'high',
        panic_score: 72,
        event_type: 'earthquake',
        confidence: 88,
        sources: 156,
        emotions: JSON.stringify({ panic: 72, fear: 67, anger: 12, sadness: 34 })
      },
      {
        title: 'Severe Storm - New York',
        description: 'Heavy rainfall and strong winds causing disruptions across NYC',
        latitude: 40.7128,
        longitude: -74.0060,
        severity: 'medium',
        panic_score: 45,
        event_type: 'storm',
        confidence: 76,
        sources: 89,
        emotions: JSON.stringify({ panic: 45, fear: 52, anger: 18, sadness: 28 })
      },
      {
        title: 'Urban Flooding - London',
        description: 'Localized flooding in downtown London affecting transport',
        latitude: 51.5074,
        longitude: -0.1278,
        severity: 'low',
        panic_score: 28,
        event_type: 'flood',
        confidence: 65,
        sources: 34,
        emotions: JSON.stringify({ panic: 28, fear: 35, anger: 42, sadness: 51 })
      },
      {
        title: 'Bushfire Alert - Sydney',
        description: 'Bushfire approaching suburban areas in Western Sydney',
        latitude: -33.8688,
        longitude: 151.2093,
        severity: 'high',
        panic_score: 68,
        event_type: 'fire',
        confidence: 84,
        sources: 178,
        emotions: JSON.stringify({ panic: 68, fear: 71, anger: 15, sadness: 38 })
      }
    ];
    
    for (const hotspot of sampleHotspots) {
      const existing = await client.query(
        'SELECT id FROM composite_hotspots WHERE title = $1',
        [hotspot.title]
      );
      
      if (existing.rows.length === 0) {
        await client.query(
          `INSERT INTO composite_hotspots 
           (title, description, latitude, longitude, severity, panic_score, event_type, confidence, sources, emotions)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
          [
            hotspot.title,
            hotspot.description,
            hotspot.latitude,
            hotspot.longitude,
            hotspot.severity,
            hotspot.panic_score,
            hotspot.event_type,
            hotspot.confidence,
            hotspot.sources,
            hotspot.emotions
          ]
        );
      }
    }
    
    console.log('✅ Sample hotspots created');
  } catch (error) {
    console.error('Error creating test data:', error);
  } finally {
    client.release();
  }
};