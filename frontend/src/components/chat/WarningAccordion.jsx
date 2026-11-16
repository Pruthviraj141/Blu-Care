import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, ChevronDown, PhoneCall } from 'lucide-react';

const WarningAccordion = ({ warningSigns = [], riskLevel = 'routine' }) => {
  const isEmergency = riskLevel === 'emergency' || riskLevel === 'high';
  // Non-emergencies start collapsed; emergency warning signs are always visible
  const [isExpanded, setIsExpanded] = useState(isEmergency);

  if (!warningSigns || warningSigns.length === 0) {
    if (!isEmergency) return null;
  }

  const getWarningText = (w) => {
    if (!w) return '';
    if (typeof w === 'string') return w;
    if (typeof w === 'object') {
      return w.sign || w.warning || w.text || w.name || '';
    }
    return String(w);
  };

  // Emergency Banner: Non-collapsible, always immediately visible
  if (isEmergency) {
    return (
      <div className="rounded-[10px] bg-rose-950/30 border border-rose-500/40 p-4 space-y-3 animate-fade-in">
        <div className="flex items-center justify-between gap-3 text-rose-400">
          <div className="flex items-center gap-2 font-semibold text-xs uppercase tracking-wider">
            <AlertCircle size={16} className="text-rose-500 shrink-0 animate-pulse" />
            <span>Emergency / Urgent Red-Flag Protocol Detected</span>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">
            IMMEDIATE ACTION
          </span>
        </div>

        <p className="text-xs text-rose-200 leading-relaxed font-medium">
          Your reported symptoms or clinical parameters require immediate emergency medical evaluation. Do not delay care.
        </p>

        {warningSigns.length > 0 && (
          <ul className="space-y-1 pl-4 list-disc text-xs text-rose-200/90 leading-relaxed">
            {warningSigns.map((w, idx) => (
              <li key={idx}>{getWarningText(w)}</li>
            ))}
          </ul>
        )}

        <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-rose-500/30">
          <span className="text-[11px] text-rose-300/80">
            Contact national emergency services or proceed to nearest casualty ward:
          </span>
          <a
            href="tel:108"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-rose-600 text-white font-semibold text-xs hover:bg-rose-500 active:scale-95 transition-all shadow-sm"
          >
            <PhoneCall size={13} />
            <span>Call SOS (108 / 112 / 911)</span>
          </a>
        </div>
      </div>
    );
  }

  // Standard Routine / Moderate Warning Signs: Accessible Collapsible Accordion
  const sectionId = 'warning-signs-content';
  const buttonId = 'warning-signs-button';

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
          <AlertTriangle size={15} className="text-[var(--severity-urgent)] shrink-0" />
          <span className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
            Warning Signs & Escalation Triggers
          </span>
          <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-secondary)]">
            {warningSigns.length}
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
          className="p-3.5 pt-1 space-y-2 text-xs border-t border-[var(--border-subtle)] animate-fade-in"
        >
          <p className="text-[11px] text-[var(--text-muted)]">
            Seek in-person medical attention promptly if you develop any of the following escalation triggers:
          </p>
          <ul className="space-y-1.5 pl-4 list-disc text-[var(--text-secondary)] leading-relaxed">
            {warningSigns.map((w, idx) => (
              <li key={idx} className="text-[var(--text-primary)]">
                {getWarningText(w)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default WarningAccordion;
