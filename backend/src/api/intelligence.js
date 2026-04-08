const express = require('express');
const router = express.Router();
const IntelligenceService = require('../services/IntelligenceService');

// Main endpoint to analyze a competitor/brand
router.post('/analyze', async (req, res) => {
  try {
    const { brand, marketType = 'B2B-SaaS-Productivity' } = req.body;

    if (!brand) {
      return res.status(400).json({ error: 'Brand name is required' });
    }

    // Analyze the brand and get competitive intelligence
    const analysis = await IntelligenceService.analyzeBrand(brand, marketType);
    
    res.json({
      status: 'success',
      data: analysis
    });
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({ 
      error: 'Failed to analyze brand', 
      message: error.message 
    });
  }
});

// Get analysis status or retrieve cached results
router.get('/analysis/:brand', async (req, res) => {
  try {
    const { brand } = req.params;
    const analysis = await IntelligenceService.getCachedAnalysis(brand);
    
    if (!analysis) {
      return res.status(404).json({ error: 'Analysis not found' });
    }

    res.json({
      status: 'success',
      data: analysis
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve analysis' });
  }
});

// Get all available signals
router.get('/signals/:brand', async (req, res) => {
  try {
    const { brand } = req.params;
    const signals = await IntelligenceService.getSignals(brand);
    
    res.json({
      status: 'success',
      signals: signals
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve signals' });
  }
});

module.exports = router;
