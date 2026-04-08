import React, { useState } from 'react';
import axios from 'axios';
import './AnalysisDashboard.css';
import CompetitorCard from '../components/CompetitorCard';
import CampaignRecommendations from '../components/CampaignRecommendations';
import { API_BASE_URL, API_HOST } from '../config/api';

function AnalysisDashboard({ brandName, onBack }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState(null);
  const [reportHistory, setReportHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('signals');
  const [askText, setAskText] = useState('');
  const [askAnswer, setAskAnswer] = useState('');
  const [followUpQuestions, setFollowUpQuestions] = useState([]);
  const [askLoading, setAskLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  React.useEffect(() => {
    const fetchAnalysis = async () => {
      setLoading(true);
      try {
        const response = await axios.post(`${API_BASE_URL}/analyze`, {
          brand_name: brandName
        });

        if (response.data.status === 'success') {
          setAnalysis(response.data.analysis);
          setReports(response.data.reports);
        }
      } catch (error) {
        console.error('Error fetching analysis:', error);
      } finally {
        setLoading(false);
      }
    };

    const fetchReportHistory = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/reports`);
        if (response.data.status === 'success') {
          setReportHistory(response.data.reports || []);
        }
      } catch (error) {
        console.error('Error loading report history:', error);
      }
    };

    fetchAnalysis();
    fetchReportHistory();
  }, [brandName]);

  const downloadReport = async (format) => {
    setDownloading(true);
    try {
      if (reports && reports[format]) {
        const fileName = `${brandName}_report.${format === 'markdown' ? 'md' : format}`;
        const downloadUrl = reports[format].startsWith('http') ? reports[format] : `${API_HOST}${reports[format]}`;
        const response = await axios.get(downloadUrl, {
          responseType: 'blob'
        });
        
        const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = blobUrl;
        link.setAttribute('download', fileName);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
      }
    } catch (error) {
      console.error('Error downloading report:', error);
      alert('Error downloading report');
    } finally {
      setDownloading(false);
    }
  };

  const answerQuestion = async (overrideQuestion = null) => {
    const questionText = (overrideQuestion ?? askText).trim();
    if (!questionText || !analysis) {
      return;
    }

    setAskLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        brand_name: brandName,
        question: questionText,
        analysis
      });

      if (response.data.status === 'success') {
        setAskAnswer(response.data.answer || 'No answer returned.');
        setFollowUpQuestions(response.data.follow_up_questions || []);
      }
    } catch (error) {
      console.error('Error answering question:', error);
      setAskAnswer(`I could not process that question right now for ${brandName}. Please try again with a more specific question about competitors, pricing, messaging, or campaign strategy.`);
      setFollowUpQuestions([
        `Which competitor is easiest for ${brandName} to beat this quarter?`,
        `What should ${brandName} say against top competitors in ad copy?`
      ]);
    } finally {
      setAskLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="analysis-dashboard loading">
        <div className="loader">
          <div className="spinner"></div>
          <p>Analyzing {brandName}...</p>
          <p className="loader-subtitle">Running competitive intelligence pipeline...</p>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="analysis-dashboard error">
        <p>Error loading analysis</p>
      </div>
    );
  }

  const {
    competitor_data = [],
    market_analysis = {},
    campaign_recommendations = {},
    guardrails = {}
  } = analysis;

  const executiveSummary = campaign_recommendations.overall_strategy || 'No summary returned yet.';
  const keyFindings = [
    ...(market_analysis.key_threats || []),
    ...(market_analysis.opportunities || [])
  ].slice(0, 6);

  const approvedGuardrails = guardrails.approved_scored || [];
  const rejectedGuardrails = guardrails.rejected_competitors || [];
  const finalSelectedGuardrails = (guardrails.final_selected_competitors || competitor_data.map((c) => c.competitor_name)).filter(Boolean);
  const formatGuardrailReason = (reason) => String(reason || '')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());

  return (
    <div className="intel-shell">
      <aside className="intel-sidebar">
        <div className="logo-wrap">
          <div className="logo-mark">⚡</div>
          <div>
            <h3>KeenFox</h3>
            <p>{brandName}</p>
          </div>
        </div>

        <nav>
          <button className={activeTab === 'signals' ? 'active' : ''} onClick={() => setActiveTab('signals')}>Signals</button>
          <button className={activeTab === 'reports' ? 'active' : ''} onClick={() => setActiveTab('reports')}>Reports</button>
          <button className={activeTab === 'campaign' ? 'active' : ''} onClick={() => setActiveTab('campaign')}>Campaign</button>
          <button className={activeTab === 'ask' ? 'active' : ''} onClick={() => setActiveTab('ask')}>Ask AI</button>
        </nav>

        <button className="back-nav" onClick={onBack}>Back to Search</button>
      </aside>

      <main className="intel-main">
        <div className="intel-header">
          <h1>Intelligence Workspace</h1>
          <div className="analysis-stats">
            <div className="stat"><span className="stat-value">{competitor_data.length}</span><span className="stat-label">Competitors</span></div>
            <div className="stat"><span className="stat-value">{analysis.signals_extracted || 0}</span><span className="stat-label">Signals</span></div>
            <div className="stat"><span className="stat-value">{market_analysis.key_threats?.length || 0}</span><span className="stat-label">Threats</span></div>
          </div>
        </div>

        <div className="analysis-content">
        {activeTab === 'signals' && (
          <div className="overview-section">
            <div className="section-header-block">
              <div>
                <p className="section-kicker">Signals</p>
                <h2>Competitive pulse for {brandName}</h2>
                <p className="section-subtitle">Brand-specific competitors, threats, and market opportunities organized in one view.</p>
              </div>
              <div className="section-chip">Live intelligence</div>
            </div>

            <div className="summary-panel">
              <div>
                <p className="summary-label">Executive Summary</p>
                <h2>{brandName} Intelligence Report</h2>
                <p className="summary-text">{executiveSummary}</p>
              </div>
              <div className="summary-meta">
                <div>
                  <span>Latest report</span>
                  <strong>{reports?.json ? 'Ready for download' : 'Not ready'}</strong>
                </div>
                <div>
                  <span>Recommendations</span>
                  <strong>{campaign_recommendations.gtm_recommendations?.length || 0}</strong>
                </div>
              </div>
            </div>

            {(guardrails.approved_count !== undefined || guardrails.rejected_count !== undefined) && (
              <div className="guardrails-panel">
                <div className="guardrails-header">
                  <div>
                    <p className="section-kicker">Guardrails</p>
                    <h2>Validation audit</h2>
                    <p className="section-subtitle">
                      This shows which competitor candidates were approved or rejected before the report was generated.
                    </p>
                  </div>
                  <div className="guardrails-chip">Grounded output</div>
                </div>

                <div className="guardrails-stats">
                  <div className="guardrail-stat approved">
                    <span>Approved</span>
                    <strong>{guardrails.approved_count ?? approvedGuardrails.length}</strong>
                  </div>
                  <div className="guardrail-stat rejected">
                    <span>Rejected</span>
                    <strong>{guardrails.rejected_count ?? rejectedGuardrails.length}</strong>
                  </div>
                  <div className="guardrail-stat total">
                    <span>Final selected</span>
                    <strong>{finalSelectedGuardrails.length}</strong>
                  </div>
                </div>

                <div className="guardrails-grid">
                  <div className="guardrails-box">
                    <h3>Approved competitors</h3>
                    <div className="guardrail-pills">
                      {(guardrails.approved_competitors || approvedGuardrails.map((item) => item.name)).map((name, idx) => (
                        <span key={idx} className="guardrail-pill approved">{name}</span>
                      ))}
                      {((guardrails.approved_competitors || approvedGuardrails).length === 0) && (
                        <span className="guardrail-empty">No approved competitors captured yet.</span>
                      )}
                    </div>
                  </div>

                  <div className="guardrails-box">
                    <h3>Rejected candidates</h3>
                    <div className="guardrail-rejections">
                      {rejectedGuardrails.map((item, idx) => (
                        <div key={idx} className="guardrail-rejection">
                          <strong>{item.name}</strong>
                          {(item.reasons || []).length > 0 ? (
                            <div className="guardrail-reason-tags">
                              {(item.reasons || []).map((reason, reasonIdx) => (
                                <span key={reasonIdx} className="guardrail-reason-tag">
                                  {formatGuardrailReason(reason)}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <p>Rejected By Guardrails</p>
                          )}
                        </div>
                      ))}
                      {rejectedGuardrails.length === 0 && (
                        <span className="guardrail-empty">No rejections were required for this run.</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="intel-grid">
              <div className="market-position">
                <h2>Market Positioning</h2>
                <div className="position-grid">
                  <div className="position-card">
                    <h3>Position</h3>
                    <p className="position-value">{market_analysis.market_position || 'N/A'}</p>
                  </div>
                  <div className="position-card">
                    <h3>Threat Level</h3>
                    <p className={`threat-${market_analysis.threat_level?.toLowerCase() || 'medium'}`}>
                      {market_analysis.threat_level || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {keyFindings.length > 0 && (
                <div className="findings-section">
                  <h2>Key Findings</h2>
                  <div className="findings-grid">
                    {keyFindings.map((finding, idx) => (
                      <div key={idx} className="finding-card">
                        {finding}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="competitors-section">
              <h2>Intelligence Signals</h2>
              <div className="competitors-grid">
                {competitor_data.map((competitor, idx) => (
                  <CompetitorCard key={idx} competitor={competitor} />
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'campaign' && (
          <div className="campaign-section-wrap">
            <div className="section-header-block">
              <div>
                <p className="section-kicker">Campaign</p>
                <h2>Activation strategy for {brandName}</h2>
                <p className="section-subtitle">Recommended messaging, channels, and go-to-market actions tied to the latest intelligence.</p>
              </div>
              <div className="section-chip">Ready to deploy</div>
            </div>
            <CampaignRecommendations brandName={brandName} recommendations={campaign_recommendations} />
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="reports-section">
            <div className="section-header-block">
              <div>
                <p className="section-kicker">Reports</p>
                <h2>Intelligence Reports</h2>
                <p className="section-subtitle">Latest run and saved history for {brandName}.</p>
              </div>
              <div className="section-chip">JSON + PDF</div>
            </div>

            {(guardrails.approved_count !== undefined || guardrails.rejected_count !== undefined) && (
              <div className="report-guardrails-card">
                <div>
                  <p className="summary-label">Guardrails summary</p>
                  <h3>Validation status for this run</h3>
                </div>
                <div className="report-guardrails-stats">
                  <span><strong>{guardrails.approved_count ?? approvedGuardrails.length}</strong> approved</span>
                  <span><strong>{guardrails.rejected_count ?? rejectedGuardrails.length}</strong> rejected</span>
                  <span><strong>{finalSelectedGuardrails.length}</strong> final</span>
                </div>

                <div className="report-guardrails-details">
                  <div className="report-guardrails-box">
                    <h4>Final selected competitors</h4>
                    <div className="guardrail-pills">
                      {finalSelectedGuardrails.map((name, idx) => (
                        <span key={idx} className="guardrail-pill approved">{name}</span>
                      ))}
                      {finalSelectedGuardrails.length === 0 && (
                        <span className="guardrail-empty">No final competitors available.</span>
                      )}
                    </div>
                  </div>

                  <div className="report-guardrails-box">
                    <h4>Rejected candidates</h4>
                    <div className="guardrail-rejections">
                      {rejectedGuardrails.map((item, idx) => (
                        <div key={idx} className="guardrail-rejection">
                          <strong>{item.name}</strong>
                          {(item.reasons || []).length > 0 ? (
                            <div className="guardrail-reason-tags">
                              {(item.reasons || []).map((reason, reasonIdx) => (
                                <span key={reasonIdx} className="guardrail-reason-tag">
                                  {formatGuardrailReason(reason)}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <p>Rejected By Guardrails</p>
                          )}
                        </div>
                      ))}
                      {rejectedGuardrails.length === 0 && (
                        <span className="guardrail-empty">No rejected candidates for this run.</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="reports-header">
              <div>
                <h3>Latest report set</h3>
                <p>Download the current intelligence pack or review the most recent saved runs.</p>
              </div>
              <div className="download-grid compact">
                {reports?.json && (
                  <button className="download-btn json" onClick={() => downloadReport('json')} disabled={downloading}>
                    JSON
                  </button>
                )}
                {reports?.pdf && (
                  <button className="download-btn pdf" onClick={() => downloadReport('pdf')} disabled={downloading}>
                    PDF
                  </button>
                )}
              </div>
            </div>

            <div className="report-cards">
              {(reportHistory.length > 0 ? reportHistory : []).map((report) => (
                <article key={report.id} className="report-card">
                  <div className="report-card-header">
                    <div>
                      <h3>{report.report_title}</h3>
                      <p>{report.summary}</p>
                    </div>
                    <span className="report-badge">complete</span>
                  </div>

                  {report.key_findings?.length > 0 && (
                    <div className="report-findings">
                      {report.key_findings.slice(0, 3).map((finding, idx) => (
                        <span key={idx}>{finding}</span>
                      ))}
                    </div>
                  )}

                  <div className="report-actions">
                    <button onClick={() => downloadReport('json')} disabled={downloading}>Open JSON</button>
                    <button onClick={() => downloadReport('pdf')} disabled={downloading}>Open PDF</button>
                  </div>
                </article>
              ))}
              {reportHistory.length === 0 && (
                <article className="report-card">
                  <div className="report-card-header">
                    <div>
                      <h3>No reports yet</h3>
                      <p>Run an analysis for {brandName} and this section will list all generated reports.</p>
                    </div>
                    <span className="report-badge">waiting</span>
                  </div>
                </article>
              )}
            </div>
          </div>
        )}

        {activeTab === 'ask' && (
          <div className="ask-section">
            <h2>Ask the Intelligence Engine</h2>
            <p>Query competitive data using natural language.</p>
            <div className="ask-box">
              <input
                type="text"
                placeholder="What are customers complaining about in competitor reviews?"
                value={askText}
                onChange={(e) => setAskText(e.target.value)}
              />
              <button onClick={() => answerQuestion()} disabled={askLoading}>{askLoading ? 'Thinking...' : 'Ask'}</button>
            </div>
            {askAnswer && <div className="ask-answer">{askAnswer}</div>}
            {followUpQuestions.length > 0 && (
              <div className="ask-followups">
                <h3>Suggested follow-up questions</h3>
                <div className="ask-followup-list">
                  {followUpQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="ask-followup-btn"
                      onClick={() => {
                        setAskText(q);
                        answerQuestion(q);
                      }}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      </main>
    </div>
  );
}

export default AnalysisDashboard;
