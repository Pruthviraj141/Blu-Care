import React from 'react';
import { ClipboardCheck, AlertCircle } from 'lucide-react';
import RiskBadge from '../ui/RiskBadge';
import AssessmentSummary from './AssessmentSummary';
import ConditionCard from './ConditionCard';
import RecommendationSection from './RecommendationSection';
import WarningAccordion from './WarningAccordion';
import SourceAccordion from './SourceAccordion';
import CareActionBar from './CareActionBar';

const AssessmentCard = ({
  assessment,
  symptomFacts = {},
  riskLevel = 'not_assessed',
  timestamp,
  actions = [],
  onExecuteAction,
  isLoading = false,
  activeActionId = null,
  ayurvedicGuidance = null,
}) => {
  if (!assessment) return null;

  const {
    case_summary = '',
    possible_conditions = [],
    recommended_actions = [],
    warning_signs = [],
    sources = [],
  } = assessment;

  const safeRiskLevel = typeof riskLevel === 'string' ? riskLevel : (riskLevel?.level || riskLevel?.risk_level || '');
  const isAssessed = Boolean(safeRiskLevel && safeRiskLevel.toLowerCase() !== 'not_assessed');

  return (
    <div className="rounded-[14px] bg-[var(--bg-card)] border border-[var(--border-strong)] p-4 sm:p-5 space-y-4 shadow-base text-[var(--text-primary)] max-w-3xl animate-fade-in">
      {/* A. Assessment Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[var(--clinical-teal)]/15 border border-[var(--clinical-teal)]/30 flex items-center justify-center text-[var(--clinical-teal)]">
            <ClipboardCheck size={16} />
          </div>
          <div>
            <h3 className="font-semibold text-sm tracking-tight text-[var(--text-primary)]">
              Clinical Assessment & Differential Triage
            </h3>
            <span className="text-[11px] text-[var(--text-muted)] font-mono">
              Evaluated: {timestamp || 'Just now'}
            </span>
          </div>
        </div>

        {/* Display urgency status ONLY when genuinely assessed */}
        {isAssessed && (
          <div className="shrink-0">
            <RiskBadge level={riskLevel} />
          </div>
        )}
      </div>

      {/* B. Patient Summary */}
      <AssessmentSummary symptomFacts={symptomFacts} caseSummary={case_summary} />

      {/* Warning Signs Accordion (or immediate emergency alert if emergency) */}
      <WarningAccordion warningSigns={warning_signs} riskLevel={riskLevel} />

      {/* C. Possible Conditions List */}
      {possible_conditions.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
              Differential Considerations ({possible_conditions.length})
            </span>
            <span className="text-[10px] text-[var(--text-muted)]">
              Primary hypothesis highlighted
            </span>
          </div>

          <div className="space-y-2.5">
            {possible_conditions.map((cond, idx) => (
              <ConditionCard key={cond.condition_id || idx} condition={cond} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* D. Recommended Care Sections */}
      <RecommendationSection
        recommendedActions={recommended_actions}
        ayurvedicGuidance={ayurvedicGuidance}
      />

      {/* F. Medical Sources Accordion */}
      <SourceAccordion sources={sources} />

      {/* Primary Action Buttons */}
      <CareActionBar
        actions={actions}
        onExecuteAction={onExecuteAction}
        isLoading={isLoading}
        activeActionId={activeActionId}
      />

      {/* Disclaimer */}
      <p className="text-[10px] text-[var(--text-muted)] italic leading-relaxed pt-2 border-t border-[var(--border-subtle)]">
        *BluCare+ is an AI clinical decision-support tool. It does not provide formal diagnostic certification. Always consult a licensed healthcare professional for clinical management.*
      </p>
    </div>
  );
};

export default AssessmentCard;
