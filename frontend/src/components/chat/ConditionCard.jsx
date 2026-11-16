import React, { useState } from 'react';
import { ChevronDown, Stethoscope, AlertTriangle, HelpCircle, BookOpen } from 'lucide-react';

const ConditionCard = ({ condition, index = 0 }) => {
  // Primary condition (index 0) defaults to open, secondary to collapsed
  const [isExpanded, setIsExpanded] = useState(index === 0);

  if (!condition) return null;

  const {
    condition_id,
    name,
    explanation,
    supporting_evidence_ids = [],
    findings_against,
    uncertainties,
    recommended_care_setting,
  } = condition;

  const contentId = `condition-content-${condition_id || index}`;
  const buttonId = `condition-button-${condition_id || index}`;

  return (
    <div
      className={`rounded-[10px] border transition-all duration-150 ${
        index === 0
          ? 'bg-[var(--bg-surface)] border-[var(--border-strong)]'
          : 'bg-[var(--bg-subtle)] border-[var(--border-subtle)] hover:border-[var(--border-strong)]'
      }`}
    >
      {/* Header clickable button */}
      <button
        id={buttonId}
        type="button"
        aria-expanded={isExpanded}
        aria-controls={contentId}
        onClick={() => setIsExpanded((prev) => !prev)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsExpanded((prev) => !prev);
          }
        }}
        className="w-full text-left p-3.5 flex items-start justify-between gap-3 cursor-pointer focus-visible:outline-2 focus-visible:outline-[var(--clinical-teal)] rounded-[10px]"
      >
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--clinical-teal)]">
              {condition_id ? condition_id.toUpperCase() : `DIFFERENTIAL ${index + 1}`}
            </span>

            {recommended_care_setting && (
              <span className="text-[11px] font-medium text-[var(--text-muted)] bg-[var(--bg-app)] px-2 py-0.5 rounded border border-[var(--border-subtle)]">
                {recommended_care_setting}
              </span>
            )}
          </div>

          <h4 className="text-sm font-semibold text-[var(--text-primary)] tracking-tight">
            {name}
          </h4>

          {/* Short summary is always visible */}
          <p className="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-2">
            {explanation}
          </p>
        </div>

        <div className="shrink-0 pt-1 text-[var(--text-muted)]">
          <ChevronDown
            size={16}
            className={`transition-transform duration-150 ${isExpanded ? 'rotate-180 text-[var(--text-primary)]' : ''}`}
          />
        </div>
      </button>

      {/* Expanded Clinical Breakdown */}
      {isExpanded && (
        <div
          id={contentId}
          role="region"
          aria-labelledby={buttonId}
          className="px-3.5 pb-3.5 pt-1 space-y-3 border-t border-[var(--border-subtle)] animate-fade-in text-xs"
        >
          {/* Full explanation */}
          <div className="space-y-1">
            <span className="font-semibold text-[var(--text-primary)] flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
              <Stethoscope size={13} className="text-[var(--clinical-teal)]" />
              Clinical Fit & Rationale
            </span>
            <p className="text-[var(--text-secondary)] leading-relaxed pl-4">
              {explanation}
            </p>
          </div>

          {/* Findings Against */}
          {findings_against && (
            <div className="space-y-1 p-2.5 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
              <span className="font-semibold text-[var(--severity-urgent)] flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
                <AlertTriangle size={13} className="shrink-0" />
                Findings Against or Atypical Features
              </span>
              <p className="text-[var(--text-secondary)] leading-relaxed pl-4">
                {findings_against}
              </p>
            </div>
          )}

          {/* Uncertainties & Testing Needed */}
          {uncertainties && (
            <div className="space-y-1 p-2.5 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
              <span className="font-semibold text-[var(--clinical-cyan)] flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
                <HelpCircle size={13} className="shrink-0" />
                Diagnostic Uncertainties & Confirmatory Testing
              </span>
              <p className="text-[var(--text-secondary)] leading-relaxed pl-4">
                {uncertainties}
              </p>
            </div>
          )}

          {/* Supporting Evidence Citations */}
          {supporting_evidence_ids && supporting_evidence_ids.length > 0 && (
            <div className="flex items-center gap-2 pt-1">
              <span className="text-[11px] text-[var(--text-muted)] flex items-center gap-1">
                <BookOpen size={12} /> Supporting Evidence:
              </span>
              <div className="flex flex-wrap gap-1">
                {supporting_evidence_ids.map((refId) => (
                  <span
                    key={refId}
                    className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-app)] border border-[var(--border-subtle)] text-[var(--text-secondary)] font-medium"
                  >
                    {refId}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ConditionCard;
