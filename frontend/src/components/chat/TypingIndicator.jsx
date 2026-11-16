import React from 'react';
import { Sparkles, Square } from 'lucide-react';

const TypingIndicator = ({ step = 'Thinking...', onStop = null }) => {
  return (
    <div
      role="status"
      aria-live="polite"
      className="inline-flex items-center gap-3 px-3.5 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] shadow-sm animate-fade-in"
    >
      <div className="flex items-center gap-1.5" aria-hidden="true">
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--clinical-teal)] animate-bounce [animation-delay:-0.3s]" />
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--clinical-teal)] animate-bounce [animation-delay:-0.15s]" />
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--clinical-teal)] animate-bounce" />
      </div>
      <div className="flex items-center gap-1.5 font-medium tracking-tight">
        <Sparkles size={13} className="text-[var(--clinical-teal)] opacity-80" />
        <span>{step}</span>
      </div>
      {onStop && (
        <button
          type="button"
          onClick={onStop}
          className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] border border-transparent hover:border-[var(--border-subtle)] transition-all cursor-pointer"
          title="Stop generation"
        >
          <Square size={10} className="fill-current" />
          <span>Stop</span>
        </button>
      )}
    </div>
  );
};

export default TypingIndicator;
