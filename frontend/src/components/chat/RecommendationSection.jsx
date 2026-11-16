import React, { useState } from 'react';
import { ChevronDown, HeartPulse, Pill, Leaf } from 'lucide-react';

const RecommendationSection = ({ recommendedActions = [], ayurvedicGuidance = null }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  if ((!recommendedActions || recommendedActions.length === 0) && !ayurvedicGuidance) {
    return null;
  }

  // Safe string extractor for recommendation items (string or object)
  const getActionText = (item) => {
    if (!item) return '';
    if (typeof item === 'string') return item;
    if (typeof item === 'object') {
      return item.action || item.text || item.recommendation || item.title || item.name || '';
    }
    return String(item);
  };

  // Group actions: general care vs conventional medical
  const generalCare = [];
  const conventionalMedical = [];

  recommendedActions.forEach((act) => {
    const rawText = getActionText(act);
    if (!rawText || !rawText.trim()) return;
    const text = rawText.toLowerCase();
    if (
      text.includes('physician') ||
      text.includes('clinic') ||
      text.includes('doctor') ||
      text.includes('hospital') ||
      text.includes('medication') ||
      text.includes('prescription') ||
      text.includes('evaluat') ||
      text.includes('consult')
    ) {
      conventionalMedical.push(act);
    } else {
      generalCare.push(act);
    }
  });

  const sectionId = 'recommendations-content';
  const buttonId = 'recommendations-button';

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
          <HeartPulse size={15} className="text-[var(--clinical-teal)] shrink-0" />
          <span className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
            Clinical Care Recommendations
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
        <div id={sectionId} role="region" aria-labelledby={buttonId} className="p-3.5 pt-1 space-y-4 text-xs border-t border-[var(--border-subtle)] animate-fade-in">
          {/* 1. General Supportive Care */}
          {generalCare.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--clinical-cyan)]" />
                Supportive Home Care & Hydration
              </span>
              <ul className="space-y-1.5 pl-3 border-l border-[var(--border-subtle)] ml-1">
                {generalCare.map((item, idx) => (
                  <li key={idx} className="text-[var(--text-primary)] leading-relaxed">
                    <span className="font-medium">{getActionText(item)}</span>
                    {item?.rationale && (
                      <span className="text-[var(--text-muted)] block text-[11px] mt-0.5">
                        {item.rationale}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 2. Conventional Medical Guidance */}
          {conventionalMedical.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-1.5">
                <Pill size={12} className="text-[var(--clinical-teal)]" />
                Conventional Clinical Evaluation
              </span>
              <ul className="space-y-1.5 pl-3 border-l border-[var(--border-subtle)] ml-1">
                {conventionalMedical.map((item, idx) => (
                  <li key={idx} className="text-[var(--text-primary)] leading-relaxed">
                    <span className="font-medium">{getActionText(item)}</span>
                    {item?.rationale && (
                      <span className="text-[var(--text-muted)] block text-[11px] mt-0.5">
                        {item.rationale}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 3. Ayurvedic & Complementary Care (if returned) */}
          {ayurvedicGuidance && (
            <div className="space-y-2 p-3 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <Leaf size={12} className="text-emerald-400" />
                Complementary Ayurvedic Guidance ({ayurvedicGuidance.condition_name})
              </span>

              {ayurvedicGuidance.traditional_classification && (
                <p className="text-[11px] text-[var(--text-muted)] italic">
                  Classification: {ayurvedicGuidance.traditional_classification}
                </p>
              )}

              {ayurvedicGuidance.dietary_and_lifestyle_care?.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[11px] font-medium text-[var(--text-secondary)]">Diet & Lifestyle:</span>
                  <ul className="list-disc list-inside text-[var(--text-primary)] space-y-0.5 pl-1">
                    {ayurvedicGuidance.dietary_and_lifestyle_care.map((diet, i) => (
                      <li key={i}>{diet}</li>
                    ))}
                  </ul>
                </div>
              )}

              {ayurvedicGuidance.safety_and_contraindications?.length > 0 && (
                <div className="text-[11px] text-amber-300 pt-1">
                  <span className="font-medium">⚠️ Safety & Contraindications:</span>
                  <ul className="list-disc list-inside space-y-0.5 pl-1 mt-0.5">
                    {ayurvedicGuidance.safety_and_contraindications.map((contra, i) => (
                      <li key={i}>{contra}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RecommendationSection;
