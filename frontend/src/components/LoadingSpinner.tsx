import React from 'react';
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  message?: string;
  fullPage?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = "Loading...", 
  fullPage = false 
}) => {
  return (
    <div className={`spinner-container ${fullPage ? 'full-page' : ''}`}>
      <div className="spinner">
        <div className="bounce1"></div>
        <div className="bounce2"></div>
        <div className="bounce3"></div>
      </div>
      {message && <div className="spinner-message">{message}</div>}
    </div>
  );
};
