import React from 'react';
import './CampaignRecommendations.css';

function CampaignRecommendations({ brandName, recommendations }) {
  const {
    overall_strategy = '',
    messaging_positioning = {},
    channel_strategy = {},
    gtm_recommendations = []
  } = recommendations;

  return (
    <div className="campaign-recommendations">
      <div className="campaign-hero">
        <div>
          <p className="section-kicker">Strategy</p>
          <h2>{brandName} activation plan</h2>
          <p className="strategy-text">A tighter view of the recommended message, channel mix, and go-to-market moves.</p>
        </div>
        <div className="campaign-hero-stats">
          <div className="campaign-stat">
            <span>Messaging</span>
            <strong>{messaging_positioning.headline ? 'Ready' : 'Pending'}</strong>
          </div>
          <div className="campaign-stat">
            <span>Channels</span>
            <strong>{channel_strategy.primary_channels?.length || 0}</strong>
          </div>
          <div className="campaign-stat">
            <span>Actions</span>
            <strong>{gtm_recommendations.length}</strong>
          </div>
        </div>
      </div>

      {overall_strategy && (
        <div className="strategy-overview">
          <h3>Overall Strategy</h3>
          <p className="strategy-text">{overall_strategy}</p>
        </div>
      )}

      {messaging_positioning.headline && (
        <div className="messaging-section">
          <h3>Messaging & Positioning</h3>
          <div className="messaging-card">
            <div className="messaging-item">
              <h3>Headline</h3>
              <p>{messaging_positioning.headline}</p>
            </div>

            {messaging_positioning.subheadline && (
              <div className="messaging-item">
                <h3>Subheadline</h3>
                <p>{messaging_positioning.subheadline}</p>
              </div>
            )}

            {messaging_positioning.differentiation && (
              <div className="messaging-item">
                <h3>Differentiation</h3>
                <p>{messaging_positioning.differentiation}</p>
              </div>
            )}

            {messaging_positioning.ad_copy && (
              <div className="ad-copy-section">
                <h3>Ad Copy Examples</h3>
                <div className="ad-copy-grid">
                  {messaging_positioning.ad_copy.email && (
                    <div className="ad-copy-item">
                      <h4>📧 Email</h4>
                      <p>{messaging_positioning.ad_copy.email}</p>
                    </div>
                  )}
                  {messaging_positioning.ad_copy.linkedin && (
                    <div className="ad-copy-item">
                      <h4>💼 LinkedIn</h4>
                      <p>{messaging_positioning.ad_copy.linkedin}</p>
                    </div>
                  )}
                  {messaging_positioning.ad_copy.website && (
                    <div className="ad-copy-item">
                      <h4>🌐 Website</h4>
                      <p>{messaging_positioning.ad_copy.website}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {channel_strategy.primary_channels && (
        <div className="channel-section">
          <h3>Channel & Targeting Strategy</h3>
          <div className="channels-grid">
            <div className="channel-card">
              <h3>Primary Channels</h3>
              <ul>
                {channel_strategy.primary_channels.map((ch, idx) => (
                  <li key={idx}>{ch}</li>
                ))}
              </ul>
            </div>
            {channel_strategy.secondary_channels && (
              <div className="channel-card secondary">
                <h3>Secondary Channels</h3>
                <ul>
                  {channel_strategy.secondary_channels.map((ch, idx) => (
                    <li key={idx}>{ch}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {channel_strategy.rationale && (
            <div className="rationale-box">
              <p><strong>Rationale:</strong> {channel_strategy.rationale}</p>
            </div>
          )}
        </div>
      )}

      {gtm_recommendations.length > 0 && (
        <div className="gtm-section">
          <h3>GTM Recommendations</h3>
          <div className="recommendations-list">
            {gtm_recommendations.map((rec, idx) => (
              <div key={idx} className="recommendation-card">
                <div className="rec-header">
                  <h3>{idx + 1}. {rec.title}</h3>
                  <span className={`priority ${rec.priority?.toLowerCase()}`}>
                    {rec.priority}
                  </span>
                </div>
                
                <p className="rec-description">{rec.description}</p>
                
                {rec.rationale && (
                  <div className="rec-detail">
                    <strong>Rationale:</strong>
                    <p>{rec.rationale}</p>
                  </div>
                )}

                {rec.expected_impact && (
                  <div className="rec-detail">
                    <strong>Expected Impact:</strong>
                    <p>{rec.expected_impact}</p>
                  </div>
                )}

                {rec.timeline && (
                  <div className="rec-detail">
                    <strong>Timeline:</strong>
                    <p>{rec.timeline}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CampaignRecommendations;
