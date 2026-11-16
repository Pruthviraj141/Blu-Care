// src/components/ui/SectionHeader.jsx
import React from 'react';
import { cn } from '../../utils/cn';

const SectionHeader = ({ title, highlightTitle, description, tag, actions, className = '' }) => {
  return (
    <div className={cn('flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-[var(--border-subtle)]', className)}>
      <div className="space-y-1 min-w-0">
        {tag && (
          <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--clinical-teal)] bg-[var(--clinical-teal)]/10 px-2 py-0.5 rounded-[4px] border border-[var(--clinical-teal)]/20 inline-block mb-1">
            {tag}
          </span>
        )}
        <h1 className="text-xl sm:text-2xl font-semibold text-[var(--text-primary)] tracking-tight">
          {title} {highlightTitle && <span className="text-[var(--clinical-teal)]">{highlightTitle}</span>}
        </h1>
        {description && <p className="text-[var(--text-secondary)] text-xs sm:text-sm leading-relaxed">{description}</p>}
      </div>

      {actions && <div className="flex items-center gap-2.5 shrink-0 mt-2 sm:mt-0">{actions}</div>}
    </div>
  );
};

export default SectionHeader;
