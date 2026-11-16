// src/components/common/Input.jsx
import React from 'react';
import { cn } from '../../utils/cn';

/**
 * Standard accessible Input with label, error, and icon support
 */
const Input = React.forwardRef(({
  label,
  error,
  icon: Icon,
  className = '',
  id,
  type = 'text',
  ...props
}, ref) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-medium text-[var(--text-secondary)] tracking-tight"
        >
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-3 text-[var(--text-muted)] pointer-events-none">
            <Icon size={16} />
          </div>
        )}
        <input
          ref={ref}
          id={inputId}
          type={type}
          className={cn(
            'w-full h-9 rounded-[6px] bg-[var(--bg-input)] border border-[var(--border-subtle)] px-3 text-xs sm:text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] transition-colors focus:border-[var(--border-focus)] focus:outline-none focus:ring-1 focus:ring-[var(--border-focus)] disabled:opacity-50',
            Icon && 'pl-9',
            error && 'border-[var(--severity-emergency)] focus:border-[var(--severity-emergency)] focus:ring-[var(--severity-emergency)]',
            className
          )}
          {...props}
        />
      </div>
      {error && (
        <p className="text-[11px] text-[var(--severity-emergency)] font-mono">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';
export default Input;

