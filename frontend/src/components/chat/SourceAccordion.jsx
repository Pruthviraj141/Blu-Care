import React, { useState } from 'react';
import { BookOpen, ChevronDown, ExternalLink } from 'lucide-react';

const SourceAccordion = ({ sources = [] }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Section 3.F: Only show the section when genuine sources exist.
  // Never display "Citations (0)" as an empty interactive button.
  if (!sources || sources.length === 0) {
    return null;
  }

  const sectionId = 'sources-content';
  const buttonId = 'sources-button';

  return (
    <div className="rounded-[10px] bg-[var(--bg-subtle)] border border-[var(--border-subtle)] overflow-hidden">
      <button
        id={buttonId}
        type="button"
        aria-expanded={isExpanded}
        aria-controls={sectionId}
        onClick={() => setIsExpanded((prev) => !prev)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsExpanded((prev) => !prev);
          }
        }}
        className="w-full text-left p-3.5 flex items-center justify-between cursor-pointer focus-visible:outline-2 focus-visible:outline-[var(--clinical-teal)] hover:bg-[var(--bg-surface)] transition-colors"
      >
        <div className="flex items-center gap-2">
          <BookOpen size={14} className="text-[var(--clinical-teal)] shrink-0" />
          <span className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
            Verified Clinical References & Guidelines
          </span>
          <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-secondary)]">
            {sources.length}
          </span>
        </div>

        <ChevronDown
          size={16}
          className={`text-[var(--text-muted)] transition-transform duration-150 ${
            isExpanded ? 'rotate-180 text-[var(--text-primary)]' : ''
          }`}
        />
      </button>

      {isExpanded && (
        <div
          id={sectionId}
          role="region"
          aria-labelledby={buttonId}
          className="p-3.5 pt-1 space-y-2.5 text-xs border-t border-[var(--border-subtle)] animate-fade-in"
        >
          {sources.map((src, idx) => {
            const title = src?.title || 'Clinical Practice Guideline';
            const id = src?.id || src?.ref_id || `REF-${idx + 1}`;
            const tag = src?.tag || src?.publisher || 'Peer-Reviewed';
            const url = src?.url || null;

            return (
              <div
                key={id || idx}
                className="p-2.5 rounded-md bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-start justify-between gap-3"
              >
                <div className="space-y-1 min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] font-semibold text-[var(--clinical-teal)] px-1.5 py-0.2 rounded bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
                      {id}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
                      {tag}
                    </span>
                  </div>
                  <p className="font-medium text-[var(--text-primary)] text-xs leading-snug">
                    {title}
                  </p>
                </div>

                {url && (
                  <a
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] text-[var(--clinical-cyan)] hover:underline shrink-0 pt-0.5"
                  >
                    <span>Source</span>
                    <ExternalLink size={11} />
                  </a>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SourceAccordion;
