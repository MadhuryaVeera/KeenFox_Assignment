import React, { useState } from 'react';
import './index.css';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import AnalysisDashboard from './pages/AnalysisDashboard';

function App() {
  const [currentPage, setCurrentPage] = useState('landing');
  const [selectedBrand, setSelectedBrand] = useState(null);

  const handleAnalyze = (brandName) => {
    setSelectedBrand(brandName);
    setCurrentPage('analysis');
  };

  return (
    <div className="app">
      <Header guardrailsStatus={currentPage === 'analysis' ? 'active' : 'ready'} />
      {currentPage === 'landing' ? (
        <Dashboard onAnalyze={handleAnalyze} />
      ) : (
        <AnalysisDashboard 
          brandName={selectedBrand}
          onBack={() => setCurrentPage('landing')}
        />
      )}
    </div>
  );
}

export default App;
