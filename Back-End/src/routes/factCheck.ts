import { Router } from 'express';
import { authenticateToken } from '../middleware/auth';
import { validateRequest, schemas } from '../middleware/validation';
import { factCheckService } from '../services/factCheckService';
import { AuthRequest } from '../types';

const router = Router();

// Submit content for fact checking
router.post('/', authenticateToken, validateRequest(schemas.factCheck), async (req: AuthRequest, res) => {
  try {
    const { content, url } = req.body;
    const userId = req.user!.id;
    
    const requestId = await factCheckService.submitFactCheck(content, url, userId);
    
    res.status(201).json({
      message: 'Fact check request submitted successfully',
      request_id: requestId,
      status: 'pending'
    });
  } catch (error) {
    console.error('Error submitting fact check:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get fact check result
router.get('/:id', authenticateToken, async (req: AuthRequest, res) => {
  try {
    const { id } = req.params;
    const userId = req.user!.id;
    
    const result = await factCheckService.getFactCheckResult(id, userId);
    
    if (!result) {
      return res.status(404).json({ error: 'Fact check request not found' });
    }
    
    res.json({ fact_check: result });
  } catch (error) {
    console.error('Error fetching fact check result:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user's fact check history
router.get('/', authenticateToken, async (req: AuthRequest, res) => {
  try {
    const userId = req.user!.id;
    const limit = parseInt(req.query.limit as string) || 50;
    
    const results = await factCheckService.getUserFactChecks(userId, limit);
    
    res.json({ fact_checks: results });
  } catch (error) {
    console.error('Error fetching fact check history:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;