import React from 'react';
import { Activity, ShieldCheck, Thermometer } from 'lucide-react';

const AssessmentSummary = ({ symptomFacts = {}, caseSummary = '' }) => {
  const symptomsObj = symptomFacts?.symptoms || {};
  const deniedList = symptomFacts?.denied_symptoms || [];

  // Filter symptoms that are marked present
  const presentSymptoms = Object.entries(symptomsObj).filter(
    ([, data]) => data?.status === 'present' || (!data?.status && data?.name)
  );

  const hasAnyData = presentSymptoms.length > 0 || deniedList.length > 0 || caseSummary;
  if (!hasAnyData) return null;

  return (
    <div className="rounded-[10px] bg-[var(--bg-subtle)] border border-[var(--border-subtle)] p-3.5 space-y-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
        <Activity size={14} className="text-[var(--clinical-teal)]" />
        <span>Patient Clinical Intake Summary</span>
      </div>

      {caseSummary && (
        <p className="text-xs leading-relaxed text-[var(--text-primary)]">
          {caseSummary}
        </p>
      )}

      {/* Reported Present Symptoms */}
      {presentSymptoms.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">
            Reported Findings
          </span>
          <div className="flex flex-wrap gap-2">
            {presentSymptoms.map(([key, data]) => {
              const name = data?.name || key;
              const duration = data?.duration ? `${data.duration}` : null;
              const severity = data?.severity ? `${data.severity}` : null;
              const temp = data?.measured_value || null;

              const details = [temp, severity, duration].filter(Boolean).join(' · ');

              return (
                <div
                  key={key}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-primary)]"
                >
                  {temp ? (
                    <Thermometer size={12} className="text-[var(--severity-urgent)] shrink-0" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--clinical-teal)] shrink-0" />
                  )}
                  <span className="font-medium capitalize">{name}</span>
                  {details && (
                    <span className="text-[11px] text-[var(--text-muted)] font-mono">
                      ({details})
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Denied Symptoms */}
      {deniedList.length > 0 && (
        <div className="space-y-1 pt-1 border-t border-[var(--border-subtle)]">
          <div className="flex items-center gap-1 text-[11px] text-[var(--text-muted)]">
            <ShieldCheck size={12} className="text-[var(--severity-routine)] shrink-0" />
            <span className="font-medium uppercase tracking-wider">Explicitly Denied:</span>
            <span className="text-[var(--text-secondary)] capitalize">
              {deniedList
                .map((d) => (typeof d === 'string' ? d : d?.name || d?.symptom || ''))
                .filter(Boolean)
                .join(', ')}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssessmentSummary;
