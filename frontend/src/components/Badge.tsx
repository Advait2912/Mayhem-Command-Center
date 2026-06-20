import React from 'react';
import './Badge.css';

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'default';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  pulse?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', pulse = false }) => {
  return (
    <span className={`badge badge-${variant} ${pulse ? 'pulse-danger' : ''}`}>
      {children}
    </span>
  );
};

/**
 * Helper to get probability badge color
 */
export const getProbabilityBadge = (prob: number) => {
  if (prob >= 0.7) return <Badge variant="danger" pulse>High Risk</Badge>;
  if (prob >= 0.4) return <Badge variant="warning">Medium Risk</Badge>;
  return <Badge variant="success">Low Risk</Badge>;
};
