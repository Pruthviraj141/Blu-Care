// src/components/common/Button.jsx
import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * World-class accessible button component
 * Adheres to BluCare+ Graphite Design System tokens
 */
const Button = React.forwardRef(({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  className = '',
  type = 'button',
  disabled = false,
  loading = false,
  icon: Icon,
  iconPosition = 'left',
  ...props
}, ref) => {
  const sizeClasses = {
    sm: 'h-7 px-2.5 text-xs gap-1.5 rounded-[6px]',
    md: 'h-9 px-3.5 text-xs sm:text-sm gap-2 rounded-[6px]',
    lg: 'h-11 px-5 text-sm sm:text-base gap-2.5 rounded-[8px]',
  };

  const variants = {
    // Primary clinical action (Restrained Steel-Blue)
    primary:
      'bg-[var(--accent-primary)] text-[#101316] font-medium hover:bg-[var(--accent-hover)] active:bg-[#607d9b] shadow-sm',
    // Secondary elevated surface
    secondary:
      'bg-[var(--bg-elevated)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:bg-[#343e49] hover:border-[var(--border-strong)] active:bg-[#252d35]',
    // Outline style
    outline:
      'bg-transparent text-[var(--text-primary)] border border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] active:bg-[var(--bg-subtle)]',
    // Subtle ghost action
    ghost:
      'bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] active:bg-[var(--bg-subtle)]',
    // Critical / Emergency action (Reserved for emergencies)
    danger:
      'bg-[var(--severity-emergency)] text-white font-medium hover:bg-[#dc2626] active:bg-[#b91c1c] shadow-sm',
    // Accent slate action
    accent:
      'bg-[var(--accent-primary)] text-[#101316] font-medium hover:bg-[var(--accent-hover)] active:bg-[#607d9b]',
  };

  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={cn(
        'inline-flex items-center justify-center font-sans tracking-tight transition-all duration-150 select-none cursor-pointer disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-2 focus-visible:outline-[var(--border-focus)] focus-visible:outline-offset-2',
        sizeClasses[size] || sizeClasses.md,
        variants[variant] || variants.primary,
        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 13 : 16} className="animate-spin shrink-0" />
      ) : (
        Icon && iconPosition === 'left' && <Icon size={size === 'sm' ? 13 : 16} className="shrink-0" />
      )}
      <span>{children}</span>
      {!loading && Icon && iconPosition === 'right' && (
        <Icon size={size === 'sm' ? 13 : 16} className="shrink-0" />
      )}
    </button>
  );
});

Button.displayName = 'Button';
export default Button;

