import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Sparkles } from 'lucide-react';

const StreamingMessage = ({ text = '', isStreaming = true }) => {
  return (
    <div className="flex items-start gap-3 w-full animate-fade-in justify-start">
      <div className="w-7 h-7 rounded-md bg-[var(--clinical-teal)]/10 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
        <Sparkles size={14} className="animate-spin" />
      </div>

      <div className="space-y-1.5 max-w-[92%] sm:max-w-[85%] md:max-w-[78%]">
        <div className="flex items-center gap-2 text-[11px] text-[var(--text-muted)] font-mono">
          <span className="font-sans font-medium text-[var(--text-secondary)]">
            BluCare Assistant
          </span>
          <span>·</span>
          <span>Streaming</span>
        </div>

        <div className="rounded-[10px] p-3.5 sm:p-4 text-xs sm:text-sm leading-relaxed bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-tl-none shadow-sm">
          <div className="prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed text-[var(--text-primary)] inline">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
          {isStreaming && (
            <span
              aria-hidden="true"
              className="inline-block w-1.5 h-4 ml-1 align-middle bg-[var(--clinical-teal)] animate-pulse"
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default StreamingMessage;
