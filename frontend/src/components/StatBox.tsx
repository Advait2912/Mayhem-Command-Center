import React from 'react';
import './StatBox.css';

interface StatBoxProps {
  label: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
  subtext?: React.ReactNode;
  highlight?: boolean;
  color?: 'blue' | 'purple' | 'green' | 'amber' | 'red';
}

export const StatBox: React.FC<StatBoxProps> = ({ 
  label, 
  value, 
  icon, 
  subtext,
  highlight = false,
  color = 'blue'
}) => {
  return (
    <div className={`stat-box glass-panel ${highlight ? `highlight-${color}` : ''}`}>
      <div className="stat-header">
        <span className="stat-label">{label}</span>
        {icon && <span className={`stat-icon color-${color}`}>{icon}</span>}
      </div>
      <div className="stat-value">{value}</div>
      {subtext && <div className="stat-subtext" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem', lineHeight: 1.2 }}>{subtext}</div>}
    </div>
  );
};
