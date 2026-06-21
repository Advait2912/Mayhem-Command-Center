import React from 'react';
import './RiskMeter.css';

interface RiskMeterProps {
  probability: number; // 0-1
}

export const RiskMeter: React.FC<RiskMeterProps> = ({ probability }) => {
  // Convert to percentage for display
  const percentage = Math.round(probability * 100);
  
  // Determine risk classification
  const getClassification = () => {
    if (probability < 0.4) return 'LOW RISK';
    if (probability < 0.7) return 'ELEVATED';
    return 'CRITICAL';
  };
  
  // Determine classification class for styling
  const getClassificationClass = () => {
    if (probability < 0.4) return 'low';
    if (probability < 0.7) return 'medium';
    return 'high';
  };
  
  // Position of the marker (0-100%)
  const markerPosition = Math.min(100, Math.max(0, percentage));
  
  const getClassificationColor = () => {
    if (probability < 0.4) return 'var(--status-success)';
    if (probability < 0.7) return 'var(--status-warning)';
    return 'var(--status-danger)';
  };
  
  return (
    <div className="risk-meter panel-live">
      <div className="risk-meter-header">
        <div className="eyebrow gradient-text">Risk Assessment</div>
        <div className={`status-tag status-tag-${getClassificationClass()}`}>
          {getClassification()}
        </div>
      </div>
      
      <div className="metric metric-lg" style={{ color: getClassificationColor() }}>{percentage}%</div>
      
      <div className="risk-meter-track">
        <div 
          className="risk-meter-fill" 
          style={{ width: `${markerPosition}%` }}
        />
        <div 
          className="risk-meter-marker" 
          style={{ left: `${markerPosition}%` }}
        />
      </div>
      
      <div className="risk-meter-scale">
        <span>0</span>
        <span>40 (watch)</span>
        <span>70 (critical)</span>
        <span>100</span>
      </div>
      
      <div className="eyebrow" style={{ marginTop: 'var(--space-2)' }}>
        calibrated, not raw model score
      </div>
    </div>
  );
};