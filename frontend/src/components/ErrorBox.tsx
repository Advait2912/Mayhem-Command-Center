import React from 'react';
import './ErrorBox.css';

interface ErrorBoxProps {
  error: Error | string;
  onRetry?: () => void;
}

export const ErrorBox: React.FC<ErrorBoxProps> = ({ error, onRetry }) => {
  const message = typeof error === 'string' ? error : error.message;
  
  return (
    <div className="error-box glass-panel">
      <div className="error-icon">⚠️</div>
      <div className="error-content">
        <h4>Something went wrong</h4>
        <p>{message}</p>
        {onRetry && (
          <button className="error-retry-btn" onClick={onRetry}>
            Try Again
          </button>
        )}
      </div>
    </div>
  );
};
