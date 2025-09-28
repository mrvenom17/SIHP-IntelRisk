import { Router } from 'express';
import { pool } from '../config/database';
import { authenticateToken } from '../middleware/auth';
import { AuthRequest } from '../types';

const router = Router();

// Export hotspots as JSON
router.get('/json', authenticateToken, async (req: AuthRequest, res) => {
  try {
    const {
      timeRange = '24h',
      severity,
      eventType,
      minConfidence = 0
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
      SELECT * FROM composite_hotspots 
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

    query += ` ORDER BY created_at DESC`;

    const result = await pool.query(query, params);
    
    const exportData = {
      export_timestamp: new Date().toISOString(),
      filters: {
        timeRange,
        severity,
        eventType,
        minConfidence
      },
      total_records: result.rows.length,
      hotspots: result.rows
    };

    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Content-Disposition', `attachment; filename="hotspots_${Date.now()}.json"`);
    res.json(exportData);
  } catch (error) {
    console.error('Error exporting JSON:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Export hotspots as CSV
router.get('/csv', authenticateToken, async (req: AuthRequest, res) => {
  try {
    const {
      timeRange = '24h',
      severity,
      eventType,
      minConfidence = 0
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
        panic_score, event_type, confidence, sources, created_at
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

    query += ` ORDER BY created_at DESC`;

    const result = await pool.query(query, params);
    
    // Generate CSV
    const headers = ['ID', 'Title', 'Description', 'Latitude', 'Longitude', 'Severity', 'Panic Score', 'Event Type', 'Confidence', 'Sources', 'Created At'];
    let csv = headers.join(',') + '\n';
    
    result.rows.forEach(row => {
      const values = [
        row.id,
        `"${row.title.replace(/"/g, '""')}"`,
        `"${(row.description || '').replace(/"/g, '""')}"`,
        row.latitude,
        row.longitude,
        row.severity,
        row.panic_score,
        row.event_type,
        row.confidence,
        row.sources,
        row.created_at
      ];
      csv += values.join(',') + '\n';
    });

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename="hotspots_${Date.now()}.csv"`);
    res.send(csv);
  } catch (error) {
    console.error('Error exporting CSV:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;