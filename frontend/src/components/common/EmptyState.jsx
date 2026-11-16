// src/components/common/EmptyState.jsx
import React from 'react';
import { cn } from '../../utils/cn';
import Button from './Button';

/**
 * Clean Empty State component for conversations, search results, hospitals
 */
const EmptyState = ({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  className = '',
  children,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center p-8 sm:p-12 rounded-[10px] border border-dashed border-[var(--border-subtle)] bg-[var(--bg-subtle)]/50',
        className
      )}
    >
      {Icon && (
        <div className="w-12 h-12 rounded-[10px] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center justify-center text-[var(--text-muted)] mb-4 shadow-sm">
          <Icon size={22} />
        </div>
      )}
      <h3 className="text-sm sm:text-base font-semibold text-[var(--text-primary)] tracking-tight">
        {title}
      </h3>
      {description && (
        <p className="text-xs sm:text-sm text-[var(--text-muted)] max-w-sm mt-1 mb-5">
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
      {children}
    </div>
  );
};

export default EmptyState;

