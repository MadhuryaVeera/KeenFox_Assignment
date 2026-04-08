const express = require('express');
const router = express.Router();
const ReportService = require('../services/ReportService');

// Generate and download report for a brand
router.post('/generate', async (req, res) => {
  try {
    const { brand, analysis } = req.body;

    if (!brand || !analysis) {
      return res.status(400).json({ error: 'Brand and analysis are required' });
    }

    const report = await ReportService.generateReport(brand, analysis);
    
    res.json({
      status: 'success',
      reportId: report.id,
      reportData: report.data
    });
  } catch (error) {
    console.error('Report generation error:', error);
    res.status(500).json({ error: 'Failed to generate report' });
  }
});

// Download report as JSON
router.get('/download/:reportId', async (req, res) => {
  try {
    const { reportId } = req.params;
    const report = await ReportService.getReport(reportId);

    if (!report) {
      return res.status(404).json({ error: 'Report not found' });
    }

    res.json(report);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve report' });
  }
});

// Get report as PDF
router.get('/pdf/:reportId', async (req, res) => {
  try {
    const { reportId } = req.params;
    const pdfBuffer = await ReportService.generatePDF(reportId);

    res.contentType('application/pdf');
    res.send(pdfBuffer);
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate PDF' });
  }
});

module.exports = router;
