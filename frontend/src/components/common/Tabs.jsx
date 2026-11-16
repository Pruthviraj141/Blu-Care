// src/components/common/Tabs.jsx
import React from 'react';
import { cn } from '../../utils/cn';

/**
 * Segmented Control / Tab Switcher component (Linear / Refero style)
 */
const Tabs = ({
  tabs = [],
  activeTab,
  onChange,
  className = '',
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'p-0.5 text-xs gap-1',
    md: 'p-1 text-xs sm:text-sm gap-1',
    lg: 'p-1 text-sm gap-1.5',
  };

  const itemSizeClasses = {
    sm: 'px-2.5 py-1 rounded-[5px]',
    md: 'px-3 py-1.5 rounded-[5px]',
    lg: 'px-4 py-2 rounded-[6px]',
  };

  return (
    <div
      role="tablist"
      className={cn(
        'inline-flex items-center rounded-[8px] bg-[var(--bg-input)] border border-[var(--border-subtle)] select-none',
        sizeClasses[size] || sizeClasses.md,
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={cn(
              'inline-flex items-center gap-1.5 font-medium transition-all duration-150 cursor-pointer whitespace-nowrap',
              itemSizeClasses[size] || itemSizeClasses.md,
              isActive
                ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-sm border border-[var(--border-subtle)]'
                : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] border border-transparent'
            )}
          >
            {tab.icon && <tab.icon size={size === 'sm' ? 12 : 14} />}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={cn(
                  'text-[10px] font-mono px-1.5 py-0.2 rounded-full',
                  isActive
                    ? 'bg-[var(--clinical-teal)]/20 text-[var(--clinical-teal)]'
                    : 'bg-white/5 text-[var(--text-muted)]'
                )}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};

export default Tabs;

