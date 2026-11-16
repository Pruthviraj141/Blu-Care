import React from 'react';
import { Sparkles, BrainCircuit, CheckCircle2 } from 'lucide-react';

const AssessmentSkeleton = ({ currentStage = 'Preparing assessment...' }) => {
  const stages = [
    { label: 'Understanding symptoms & intake facts', active: true, done: true },
    { label: 'Reviewing clinical guidelines & evidence', active: true, done: true },
    { label: currentStage || 'Synthesizing differential assessment', active: true, done: false },
  ];

  return (
    <div
      role="status"
      aria-live="polite"
      className="rounded-[14px] bg-[var(--bg-subtle)] border border-[var(--border-strong)] p-5 space-y-4 max-w-2xl animate-fade-in"
    >
      <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <BrainCircuit size={18} className="text-[var(--clinical-teal)] animate-pulse" />
          <h4 className="font-semibold text-sm text-[var(--text-primary)]">
            Clinical Decision-Support In Progress
          </h4>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] font-mono">
          <Sparkles size={13} className="text-[var(--clinical-teal)]" />
          <span>BluCare Core</span>
        </div>
      </div>

      {/* Progress Stages */}
      <div className="space-y-2 py-1">
        {stages.map((st, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            {st.done ? (
              <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
            ) : (
              <span className="w-3.5 h-3.5 rounded-full border-2 border-[var(--clinical-teal)] border-t-transparent animate-spin shrink-0" />
            )}
            <span
              className={
                st.done
                  ? 'text-[var(--text-secondary)] line-through opacity-70'
                  : 'text-[var(--text-primary)] font-medium'
              }
            >
              {st.label}
            </span>
          </div>
        ))}
      </div>

      {/* Structured Pulse Skeletons */}
      <div className="space-y-3 pt-2">
        <div className="h-4 w-3/4 rounded bg-[var(--bg-elevated)] animate-pulse" />
        <div className="h-16 w-full rounded-[10px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] animate-pulse" />
        <div className="h-20 w-full rounded-[10px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] animate-pulse" />
      </div>
    </div>
  );
};

export default AssessmentSkeleton;
