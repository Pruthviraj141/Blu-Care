// src/components/common/Badge.jsx
import React from 'react';
import { cn } from '../../utils/cn';

/**
 * Universal badge component for triage, status tags, and metadata
 */
const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
  ...props
}) => {
  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5 gap-1 rounded-[4px] font-mono',
    md: 'text-[11px] px-2 py-0.5 gap-1.5 rounded-[5px] font-mono',
    lg: 'text-xs px-2.5 py-1 gap-1.5 rounded-[6px] font-medium',
  };

  const variants = {
    default:
      'bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-subtle)]',
    steel:
      'bg-[var(--accent-primary)]/15 text-[var(--accent-primary)] border border-[var(--accent-primary)]/30 font-medium',
    teal:
      'bg-[var(--accent-primary)]/15 text-[var(--accent-primary)] border border-[var(--accent-primary)]/30',
    cyan:
      'bg-[var(--accent-hover)]/15 text-[var(--accent-hover)] border border-[var(--accent-hover)]/30',
    emergency:
      'bg-[var(--severity-emergency)]/15 text-[var(--severity-emergency)] border border-[var(--severity-emergency)]/30 font-semibold',
    warning:
      'bg-[var(--severity-warning)]/15 text-[var(--severity-warning)] border border-[var(--severity-warning)]/30 font-semibold',
    routine:
      'bg-[var(--severity-routine)]/15 text-[var(--severity-routine)] border border-[var(--severity-routine)]/30 font-medium',
    muted:
      'bg-transparent text-[var(--text-muted)] border border-[var(--border-subtle)]',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center font-normal tracking-tight select-none shrink-0',
        sizeClasses[size] || sizeClasses.md,
        variants[variant] || variants.default,
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            'w-1.5 h-1.5 rounded-full shrink-0',
            variant === 'emergency' && 'bg-[var(--severity-emergency)]',
            variant === 'warning' && 'bg-[var(--severity-warning)]',
            variant === 'routine' && 'bg-[var(--severity-routine)]',
            variant === 'teal' && 'bg-[var(--clinical-teal)]',
            variant === 'cyan' && 'bg-[var(--clinical-cyan)]',
            variant === 'default' && 'bg-[var(--text-muted)]'
          )}
        />
      )}
      <span>{children}</span>
    </span>
  );
};

export default Badge;

