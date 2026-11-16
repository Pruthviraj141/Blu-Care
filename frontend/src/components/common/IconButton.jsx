// src/components/common/IconButton.jsx
import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Compact Icon Button for toolbars, dismiss buttons, header actions
 */
const IconButton = React.forwardRef(({
  icon: Icon,
  onClick,
  variant = 'ghost',
  size = 'md',
  className = '',
  type = 'button',
  disabled = false,
  loading = false,
  title,
  'aria-label': ariaLabel,
  ...props
}, ref) => {
  const sizeClasses = {
    xs: 'w-6 h-6 rounded-[5px]',
    sm: 'w-7 h-7 rounded-[6px]',
    md: 'w-8 h-8 rounded-[6px]',
    lg: 'w-10 h-10 rounded-[8px]',
  };

  const iconSizes = {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
  };

  const variants = {
    ghost:
      'bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] active:bg-[var(--bg-subtle)]',
    secondary:
      'bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)]',
    outline:
      'bg-transparent text-[var(--text-primary)] border border-[var(--border-strong)] hover:bg-[var(--bg-elevated)]',
    primary:
      'bg-[var(--accent-primary)] text-[#101316] hover:bg-[var(--accent-hover)]',
    danger:
      'bg-transparent text-[var(--severity-emergency)] hover:bg-[var(--severity-emergency)]/15',
  };

  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      title={title || ariaLabel}
      aria-label={ariaLabel || title}
      className={cn(
        'inline-flex items-center justify-center shrink-0 transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-2 focus-visible:outline-[var(--border-focus)]',
        sizeClasses[size] || sizeClasses.md,
        variants[variant] || variants.ghost,
        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 size={iconSizes[size] || 16} className="animate-spin" />
      ) : (
        Icon && <Icon size={iconSizes[size] || 16} />
      )}
    </button>
  );
});

IconButton.displayName = 'IconButton';
export default IconButton;

