import React from 'react';
import './CompetitorCard.css';

function CompetitorCard({ competitor }) {
  const insights = competitor.insights || {};
  const threatColor = {
    high: '#e74c3c',
    medium: '#f39c12',
    low: '#27ae60'
  };

  return (
    <div className="competitor-card">
      <div className="competitor-header">
        <div>
          <p className="competitor-kicker">Competitor</p>
          <h3>{competitor.competitor_name}</h3>
        </div>
        <span
          className="threat-badge"
          style={{ backgroundColor: threatColor[competitor.threat_level] || '#999' }}
        >
          {competitor.threat_level?.toUpperCase() || 'MEDIUM'}
        </span>
      </div>

      {insights.key_features && insights.key_features.length > 0 && (
        <div className="competitor-section">
          <h4>Product signals</h4>
          <ul>
            {insights.key_features.slice(0, 5).map((feature, idx) => (
              <li key={idx}>{feature}</li>
            ))}
          </ul>
        </div>
      )}

      {insights.messaging_themes && insights.messaging_themes.length > 0 && (
        <div className="competitor-section">
          <h4>Messaging signals</h4>
          <ul>
            {insights.messaging_themes.slice(0, 3).map((msg, idx) => (
              <li key={idx}>{msg}</li>
            ))}
          </ul>
        </div>
      )}

      {insights.market_gaps && insights.market_gaps.length > 0 && (
        <div className="competitor-section weaknesses">
          <h4>Weaknesses</h4>
          <ul>
            {insights.market_gaps.slice(0, 3).map((gap, idx) => (
              <li key={idx}>{gap}</li>
            ))}
          </ul>
        </div>
      )}

      {competitor.website && (
        <a href={competitor.website} target="_blank" rel="noopener noreferrer" className="website-link">
          Visit Website →
        </a>
      )}
    </div>
  );
}

export default CompetitorCard;
