import React, { useState } from 'react';
import axios from 'axios';
import './Dashboard.css';
import { API_BASE_URL } from '../config/api';

function Dashboard({ onAnalyze }) {
  const [brandName, setBrandName] = useState('');
  const [loading, setLoading] = useState(false);
  const [backendReady, setBackendReady] = useState(null);
  const guardrailsActive = backendReady !== false;

  React.useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 });
        setBackendReady(response?.data?.status === 'healthy');
      } catch {
        setBackendReady(false);
      }
    };

    checkHealth();
  }, []);

  const handleAnalysis = async (brandName) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, {
        brand_name: brandName
      });
      
      if (response.data.status === 'success') {
        onAnalyze(brandName);
      }
    } catch (error) {
      console.error('Error analyzing brand:', error);
      const serverMessage = error?.response?.data?.error;
      const message = serverMessage
        ? `Analyze failed: ${serverMessage}`
        : 'Cannot reach backend. Start backend server on http://127.0.0.1:5000 and try again.';
      alert(message);
    } finally {
      setLoading(false);
    }
  };

  const submitFromInput = (e) => {
    e.preventDefault();
    if (!brandName.trim() || loading) {
      return;
    }
    handleAnalysis(brandName.trim());
  };

  return (
    <div className="landing-page">
      <div className="landing-glow" />
      <div className="landing-container">
        <div className="badge">AI-Powered Competitive Intelligence</div>
        <h1>
          Know your <span>competitors</span>
          <br />
          before they know <em>you</em>
        </h1>
        <p>
          Enter any brand name and get instant competitor discovery,
          strategic signal extraction, and AI-generated campaign recommendations.
        </p>

        <div className={`backend-pill ${backendReady === false ? 'down' : 'ok'}`}>
          {guardrailsActive ? 'Guardrails Ready' : 'Guardrails Offline'}
        </div>

        <form className="brand-form" onSubmit={submitFromInput}>
          <input
            type="text"
            placeholder="Enter a brand name (e.g. Shopify)"
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            disabled={loading || backendReady === false}
          />
          <button type="submit" disabled={loading || !brandName.trim() || backendReady === false}>
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>

        <div className="quick-brands">
          <span>Try:</span>
          {['Coca-Cola', 'Nike', 'Notion', 'Shopify', 'Tesla', 'Spotify'].map((brand) => (
            <button
              key={brand}
              type="button"
              onClick={() => handleAnalysis(brand)}
              disabled={loading}
            >
              {brand}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
