import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SearchBrand.css';
import { API_BASE_URL } from '../config/api';

function SearchBrand() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/search`, {
        params: { q: searchQuery }
      });

      if (response.data.status === 'success') {
        setResults(response.data.results);
      }
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-brand">
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          placeholder="Search analyzed brands..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results.length > 0 && (
        <div className="search-results">
          <h3>Results ({results.length})</h3>
          <div className="results-grid">
            {results.map((result) => (
              <div key={result.id} className="result-item">
                <h4>{result.name}</h4>
                <p className="result-meta">
                  <span>{result.industry || 'N/A'}</span>
                  <span>{result.market_segment || 'N/A'}</span>
                </p>
                <a href={result.website} target="_blank" rel="noopener noreferrer">
                  Visit →
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {searchQuery && results.length === 0 && !loading && (
        <p className="no-results">No results found for "{searchQuery}"</p>
      )}
    </div>
  );
}

export default SearchBrand;
