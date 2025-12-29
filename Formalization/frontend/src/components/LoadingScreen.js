import React from 'react';
import Logo from './Logo';

const LoadingScreen = ({ message = 'Loading...' }) => {
  return (
    <div className="loading-screen">
      <div className="loading-content">
        <div className="loading-logo">
          <Logo size="large" />
        </div>
        <div className="loading-text">
          <h2>Bear Systems</h2>
          <p>Agentic HR System</p>
        </div>
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
        <p className="loading-message">{message}</p>
      </div>
    </div>
  );
};

export default LoadingScreen;
