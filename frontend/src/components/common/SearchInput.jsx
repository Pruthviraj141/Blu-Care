// src/components/common/SearchInput.jsx
import React from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Standard Search input with clear button
 */
const SearchInput = React.forwardRef(({
  value,
  onChange,
  onClear,
  placeholder = 'Search...',
  className = '',
  size = 'md',
  ...props
}, ref) => {
  const sizeClasses = {
    sm: 'h-8 text-xs pl-8 pr-7',
    md: 'h-9 text-xs sm:text-sm pl-9 pr-8',
    lg: 'h-10 text-sm pl-10 pr-9',
  };

  const iconSizes = {
    sm: 14,
    md: 15,
    lg: 18,
  };

  return (
    <div className="relative flex items-center w-full">
      <div className="absolute left-2.5 sm:left-3 text-[var(--text-muted)] pointer-events-none">
        <Search size={iconSizes[size] || 15} />
      </div>
      <input
        ref={ref}
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={cn(
          'w-full rounded-[6px] bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder-[var(--text-muted)] transition-colors focus:border-[var(--border-focus)] focus:outline-none focus:ring-1 focus:ring-[var(--border-focus)]',
          sizeClasses[size] || sizeClasses.md,
          className
        )}
        {...props}
      />
      {value && onClear && (
        <button
          type="button"
          onClick={onClear}
          className="absolute right-2.5 text-[var(--text-muted)] hover:text-[var(--text-primary)] p-0.5 rounded cursor-pointer"
          title="Clear search"
          aria-label="Clear search"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
});

SearchInput.displayName = 'SearchInput';
export default SearchInput;

