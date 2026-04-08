require('dotenv').config();
const express = require('express');
const cors = require('cors');
const fileUpload = require('express-fileupload');
const path = require('path');

// Import routes
const intelligenceRoutes = require('./src/api/intelligence');
const reportRoutes = require('./src/api/reports');
const campaignRoutes = require('./src/api/campaigns');

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(fileUpload());

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'KeenFox Intelligence System is running' });
});

// API Routes
app.use('/api/intelligence', intelligenceRoutes);
app.use('/api/reports', reportRoutes);
app.use('/api/campaigns', campaignRoutes);

// Download endpoint for reports
app.get('/api/download/:reportId', (req, res) => {
  try {
    const reportId = req.params.reportId;
    const filePath = path.join(__dirname, 'reports', `${reportId}.json`);
    res.download(filePath);
  } catch (error) {
    res.status(500).json({ error: 'Failed to download report' });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err);
  res.status(err.status || 500).json({ 
    error: err.message || 'Internal Server Error' 
  });
});

app.listen(PORT, () => {
  console.log(`KeenFox Intelligence System running on port ${PORT}`);
});
