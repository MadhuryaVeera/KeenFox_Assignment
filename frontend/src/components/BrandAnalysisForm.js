import React, { useState } from 'react';
import './BrandAnalysisForm.css';

function BrandAnalysisForm({ onSubmit, loading }) {
  const [brandName, setBrandName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (brandName.trim()) {
      onSubmit(brandName.trim());
      setBrandName('');
    }
  };

  return (
    <form className="brand-analysis-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <input
          type="text"
          placeholder="Enter a brand name (e.g. Coca-Cola)"
          value={brandName}
          onChange={(e) => setBrandName(e.target.value)}
          disabled={loading}
          className="form-input"
        />
        <button
          type="submit"
          disabled={loading || !brandName.trim()}
          className="form-button"
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </form>
  );
}

export default BrandAnalysisForm;
