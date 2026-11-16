import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Sparkles, Copy, Check, FileSearch } from 'lucide-react';
import AssessmentCard from './AssessmentCard';
import FacilityCardContainer from './FacilityCard';

const ChatMessage = ({
  message,
  onExecuteAction,
  onOpenCitation,
  copiedMsgId,
  onCopyText,
  isLoadingAction = false,
  activeActionId = null,
}) => {
  if (!message) return null;

  const isUser = message.role === 'user';
  const hasAssessment = Boolean(message.assessment);
  const hasFacilities = Boolean(
    (message.facilities && message.facilities.length > 0) ||
      (message.text && (
        message.text.includes('Verified Healthcare Clinics & Hospitals Near You') ||
        message.text.includes('Top 5 Nearest Healthcare Facilities') ||
        message.text.includes('Verified Facilities (Ranked Nearest First)') ||
        message.text.includes('Verified OpenStreetMap Facilities') ||
        message.text.includes('Directions](https://www.google.com/maps/dir')
      ))
  );

  return (
    <div
      className={`flex items-start gap-3 w-full animate-fade-in ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      {/* Bot Icon */}
      {!isUser && (
        <div className="w-7 h-7 rounded-md bg-[var(--clinical-teal)]/10 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
          <Sparkles size={14} />
        </div>
      )}

      {/* Content Container */}
      <div className={`space-y-1.5 max-w-[92%] sm:max-w-[85%] md:max-w-[78%]`}>
        {/* Header Metadata */}
        <div
          className={`flex items-center gap-2 text-[11px] text-[var(--text-muted)] font-mono ${
            isUser ? 'justify-end' : 'justify-start'
          }`}
        >
          <span className="font-sans font-medium text-[var(--text-secondary)]">
            {isUser ? 'You' : 'BluCare Assistant'}
          </span>
          <span>·</span>
          <span>{message.timestamp}</span>
        </div>

        {/* Branch 1: Structured Clinical Assessment */}
        {hasAssessment ? (
          <AssessmentCard
            assessment={message.assessment}
            symptomFacts={message.symptom_facts}
            riskLevel={message.risk_level}
            timestamp={message.timestamp}
            actions={message.actions}
            onExecuteAction={onExecuteAction}
            isLoading={isLoadingAction}
            activeActionId={activeActionId}
            ayurvedicGuidance={message.ayurvedic_guidance}
          />
        ) : hasFacilities ? (
          /* Branch 2: Structured Nearby Facilities Container */
          <FacilityCardContainer
            facilities={message.facilities || []}
            externalSearch={message.external_search || {}}
            fallbackText={message.text}
          />
        ) : (
          /* Branch 3: Standard Conversational Bubble (Linear / Apple Notes style) */
          <div
            className={`rounded-[10px] p-3.5 sm:p-4 text-xs sm:text-sm leading-relaxed transition-all shadow-sm ${
              isUser
                ? 'bg-[var(--bg-elevated)] border border-[var(--border-strong)] text-[var(--text-primary)] rounded-tr-none'
                : 'bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-tl-none'
            }`}
          >
            <div className="prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed text-[var(--text-primary)] font-normal">
              <ReactMarkdown>{message.text}</ReactMarkdown>
            </div>

            {/* Bottom Actions for Bot: Copy text & Citation link */}
            {!isUser && (
              <div className="mt-2.5 pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-[11px] text-[var(--text-muted)]">
                <div className="flex items-center gap-2">
                  {message.sources && message.sources.length > 0 && (
                    <button
                      type="button"
                      onClick={() => onOpenCitation && onOpenCitation(message.sources[0])}
                      className="inline-flex items-center gap-1 text-[var(--clinical-teal)] hover:underline cursor-pointer"
                    >
                      <FileSearch size={11} />
                      <span>{message.sources.length} Verified Sources</span>
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => onCopyText && onCopyText(message.text, message.id)}
                  className="p-1 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
                  title="Copy message"
                >
                  {copiedMsgId === message.id ? (
                    <Check size={12} className="text-emerald-400" />
                  ) : (
                    <Copy size={12} />
                  )}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* User Icon */}
      {isUser && (
        <div className="w-7 h-7 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-strong)] text-[var(--text-secondary)] flex items-center justify-center shrink-0 mt-0.5">
          <User size={14} />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
