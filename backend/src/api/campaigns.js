const express = require('express');
const router = express.Router();
const CampaignService = require('../services/CampaignService');

// Generate campaign recommendations based on competitive analysis
router.post('/recommendations', async (req, res) => {
  try {
    const { brand, competitors, targetMarket = 'B2B-SaaS' } = req.body;

    if (!brand || !competitors) {
      return res.status(400).json({ 
        error: 'Brand and competitors array are required' 
      });
    }

    const recommendations = await CampaignService.generateRecommendations(
      brand,
      competitors,
      targetMarket
    );

    res.json({
      status: 'success',
      recommendations: recommendations
    });
  } catch (error) {
    console.error('Campaign recommendations error:', error);
    res.status(500).json({ 
      error: 'Failed to generate recommendations',
      message: error.message 
    });
  }
});

// Get GTM strategy recommendations
router.post('/gtm-strategy', async (req, res) => {
  try {
    const { brand, competitiveAnalysis } = req.body;

    if (!brand || !competitiveAnalysis) {
      return res.status(400).json({ 
        error: 'Brand and competitiveAnalysis are required' 
      });
    }

    const strategy = await CampaignService.generateGTMStrategy(
      brand,
      competitiveAnalysis
    );

    res.json({
      status: 'success',
      strategy: strategy
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate GTM strategy' });
  }
});

module.exports = router;
