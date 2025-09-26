import { Router } from 'express';
import { pool } from '../config/database';
import { authenticateToken, requireAnalyst } from '../middleware/auth';
import { validateRequest, schemas } from '../middleware/validation';

const router = Router();

// Get all composite hotspots with filtering
router.get('/composite', authenticateToken, async (req, res) => {
  try {
    const {
      timeRange = '24h',
      severity,
      eventType,
      minConfidence = 0,
      limit = 100,
      offset = 0
    } = req.query;

    let timeFilter = '';
    switch (timeRange) {
      case '1h':
        timeFilter = "AND created_at >= NOW() - INTERVAL '1 hour'";
        break;
      case '6h':
        timeFilter = "AND created_at >= NOW() - INTERVAL '6 hours'";
        break;
      case '24h':
        timeFilter = "AND created_at >= NOW() - INTERVAL '24 hours'";
        break;
      case '7d':
        timeFilter = "AND created_at >= NOW() - INTERVAL '7 days'";
        break;
      case '30d':
        timeFilter = "AND created_at >= NOW() - INTERVAL '30 days'";
        break;
    }

    let query = `
      SELECT 
        id, title, description, latitude, longitude, severity, 
        panic_score, event_type, confidence, sources, emotions,
        contributing_reports, created_at, updated_at
      FROM composite_hotspots 
      WHERE confidence >= $1 
      ${timeFilter}
    `;
    
    const params: any[] = [minConfidence];
    let paramIndex = 2;

    if (severity) {
      query += ` AND severity = $${paramIndex}`;
      params.push(severity);
      paramIndex++;
    }

    if (eventType) {
      query += ` AND event_type = $${paramIndex}`;
      params.push(eventType);
      paramIndex++;
    }

    query += ` ORDER BY created_at DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    params.push(limit, offset);

    const result = await pool.query(query, params);
    
    // Transform database results to match frontend expectations
    const hotspots = result.rows.map(row => ({
      id: row.id,
      title: row.title,
      description: row.description,
      latitude: row.latitude,
      longitude: row.longitude,
      severity: row.severity,
      panicScore: row.panic_score,
      eventType: row.event_type,
      confidence: row.confidence,
      sources: row.sources,
      emotions: row.emotions,
      timestamp: row.created_at,
      contributingReports: row.contributing_reports
    }));
    
    res.json({
      hotspots,
      total: result.rows.length,
      filters: {
        timeRange,
        severity,
        eventType,
        minConfidence
      }
    });
  } catch (error) {
    console.error('Error fetching composite hotspots:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get hotspot by ID
router.get('/composite/:id', authenticateToken, async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await pool.query(
      `SELECT 
        id, title, description, latitude, longitude, severity, 
        panic_score, event_type, confidence, sources, emotions,
        contributing_reports, created_at, updated_at
       FROM composite_hotspots WHERE id = $1`,
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Hotspot not found' });
    }
    
    const row = result.rows[0];
    const hotspot = {
      id: row.id,
      title: row.title,
      description: row.description,
      latitude: row.latitude,
      longitude: row.longitude,
      severity: row.severity,
      panicScore: row.panic_score,
      eventType: row.event_type,
      confidence: row.confidence,
      sources: row.sources,
      emotions: row.emotions,
      timestamp: row.created_at,
      contributingReports: row.contributing_reports
    };
    
    res.json({ hotspot });
  } catch (error) {
    console.error('Error fetching hotspot:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create human hotspot (analysts and admins only)
router.post('/human', authenticateToken, requireAnalyst, validateRequest(schemas.hotspot), async (req, res) => {
  try {
    const { title, description, latitude, longitude, severity, event_type } = req.body;
    const userId = req.user!.id;
    
    const result = await pool.query(
      `INSERT INTO human_hotspots (title, description, latitude, longitude, severity, event_type, created_by)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING *`,
      [title, description, latitude, longitude, severity, event_type, userId]
    );
    
    res.status(201).json({
      message: 'Human hotspot created successfully',
      hotspot: result.rows[0]
    });
  } catch (error) {
    console.error('Error creating human hotspot:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get statistics
router.get('/stats', authenticateToken, async (req, res) => {
  try {
    const stats = await pool.query(`
      SELECT 
        COUNT(*) as total_hotspots,
        COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_count,
        COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_count,
        COUNT(CASE WHEN severity = 'medium' THEN 1 END) as medium_count,
        COUNT(CASE WHEN severity = 'low' THEN 1 END) as low_count,
        AVG(panic_score) as avg_panic_score,
        AVG(confidence) as avg_confidence
      FROM composite_hotspots 
      WHERE created_at >= NOW() - INTERVAL '24 hours'
    `);
    
    const eventTypes = await pool.query(`
      SELECT event_type, COUNT(*) as count
      FROM composite_hotspots 
      WHERE created_at >= NOW() - INTERVAL '24 hours'
      GROUP BY event_type
    `);
    
    res.json({
      summary: stats.rows[0],
      event_distribution: eventTypes.rows
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;