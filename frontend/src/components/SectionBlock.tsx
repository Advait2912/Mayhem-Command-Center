import React from 'react';
import './SectionBlock.css';

interface SectionBlockProps {
  title: React.ReactNode;
  icon?: React.ReactNode;
  children: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export const SectionBlock: React.FC<SectionBlockProps> = ({ 
  title, 
  icon, 
  children, 
  action,
  className = '',
  noPadding = false
}) => {
  return (
    <section className={`section-block glass-panel ${className}`}>
      <header className="section-header">
        <div className="section-title-wrap">
          {icon && <span className="section-icon">{icon}</span>}
          <h3 className="section-title">{title}</h3>
        </div>
        {action && <div className="section-action">{action}</div>}
      </header>
      <div className={`section-content ${noPadding ? 'no-padding' : ''}`}>
        {children}
      </div>
    </section>
  );
};
