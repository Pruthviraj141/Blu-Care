// src/components/ui/GlassCard.jsx
import React from 'react';
import Card from '../common/Card';

/**
 * Backward compatibility wrapper for GlassCard
 * Migrated to clean, non-bloated graphite Card primitive
 */
const GlassCard = ({
  children,
  className = '',
  hoverable = false,
  noisy = false,
  onClick,
  ...props
}) => {
  return (
    <Card
      onClick={onClick}
      hoverable={hoverable}
      className={className}
      {...props}
    >
      {children}
    </Card>
  );
};

export default GlassCard;
