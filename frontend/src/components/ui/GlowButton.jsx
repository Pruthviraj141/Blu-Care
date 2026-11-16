// src/components/ui/GlowButton.jsx
import React from 'react';
import Button from '../common/Button';

/**
 * Backward compatibility wrapper for GlowButton
 * Migrated to clean, non-glowing BluCare+ Button primitive
 */
const GlowButton = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  className = '',
  type = 'button',
  disabled = false,
  loading = false,
  ...props
}) => {
  // Map old neon variants to clean clinical design system
  const variantMap = {
    primary: 'primary',
    secondary: 'secondary',
    accent: 'secondary',
    danger: 'danger',
  };

  return (
    <Button
      type={type}
      disabled={disabled}
      loading={loading}
      onClick={onClick}
      variant={variantMap[variant] || 'primary'}
      size={size}
      className={className}
      {...props}
    >
      {children}
    </Button>
  );
};

export default GlowButton;
