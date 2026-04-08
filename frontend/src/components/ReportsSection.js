import React from 'react';
import './ReportsSection.css';

function ReportsSection({ reports, loading }) {
  if (reports.length === 0) {
    return (
      <div className="reports-section empty">
        <p>No reports generated yet. Analyze a brand to generate reports!</p>
      </div>
    );
  }

  return (
    <div className="reports-section">
      <div className="reports-grid">
        {reports.map((report, idx) => (
          <div key={idx} className="report-card">
            <h3>{report.report_title}</h3>
            <div className="report-stats">
              <span>{report.competitors_analyzed} Competitors</span>
              <span>{report.signals_extracted} Signals</span>
            </div>
            <p>{report.summary}</p>
            <a href={report.file_path} download className="download-link">
              Download Report
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ReportsSection;
