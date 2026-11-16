// src/components/common/Card.jsx
import React from 'react';
import { cn } from '../../utils/cn';

/**
 * Universal Card primitive matching graphite neutral surface tokens
 * Replaces old oversized rounded-3xl glass cards
 */
const Card = React.forwardRef(({
  children,
  className = '',
  hoverable = false,
  elevated = false,
  bordered = true,
  onClick,
  ...props
}, ref) => {
  return (
    <div
      ref={ref}
      onClick={onClick}
      className={cn(
        'rounded-[10px] p-4 sm:p-5 transition-all duration-150',
        elevated ? 'bg-[var(--bg-elevated)]' : 'bg-[var(--bg-surface)]',
        bordered && 'border border-[var(--border-subtle)]',
        hoverable && 'hover:border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

Card.displayName = 'Card';
export default Card;

