// src/components/common/Accordion.jsx
import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Collapsible Accordion item with smooth disclosure and accessible state
 */
const Accordion = ({
  title,
  subtitle,
  icon: Icon,
  badge,
  children,
  defaultOpen = false,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div
      className={cn(
        'rounded-[8px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] overflow-hidden transition-all duration-150',
        isOpen && 'border-[var(--border-strong)]',
        className
      )}
    >
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        className="w-full flex items-center justify-between p-3.5 text-left hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer select-none"
      >
        <div className="flex items-center gap-2.5 min-w-0 pr-2">
          {Icon && (
            <div className="text-[var(--text-secondary)] shrink-0">
              <Icon size={16} />
            </div>
          )}
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs sm:text-sm font-medium text-[var(--text-primary)] truncate">
                {title}
              </span>
              {badge}
            </div>
            {subtitle && (
              <p className="text-[11px] text-[var(--text-muted)] truncate mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        <ChevronDown
          size={16}
          className={cn(
            'text-[var(--text-muted)] shrink-0 transition-transform duration-200',
            isOpen && 'rotate-180 text-[var(--text-primary)]'
          )}
        />
      </button>

      {isOpen && (
        <div className="p-3.5 pt-0 border-t border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] leading-relaxed animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
};

export default Accordion;

