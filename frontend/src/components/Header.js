import React from 'react';
import './Header.css';

function Header({ guardrailsStatus = 'ready' }) {
  const badgeText = guardrailsStatus === 'active' ? 'Guardrails Active' : 'Guardrails Ready';

  return (
    <header className="header">
      <div className="header-container">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">⚡</span>
            <h1>KeenFox</h1>
          </div>
          <p className="tagline">AI-Powered Competitive Intelligence</p>
          <span className="guardrails-badge">{badgeText}</span>
        </div>
        <nav className="header-nav">
          <a href="#features">Features</a>
          <a href="#about">About</a>
        </nav>
      </div>
    </header>
  );
}

export default Header;
