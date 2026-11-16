import React from 'react';
import { Leaf, Building2, Loader2 } from 'lucide-react';

const CareActionBar = ({
  actions = [],
  onExecuteAction,
  isLoading = false,
  activeActionId = null,
}) => {
  if (!actions || actions.length === 0) return null;

  const handleClick = (actionId, conditionId) => {
    if (isLoading) return;
    if (typeof onExecuteAction === 'function') {
      onExecuteAction(actionId, conditionId);
    }
  };

  return (
    <div className="pt-3 border-t border-[var(--border-subtle)] space-y-2">
      <div className="text-[11px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
        Next Recommended Care Steps
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        {actions.map((act) => {
          const isAyu = act.id === 'GET_AYURVEDIC_GUIDANCE';
          const isCurrentLoading = isLoading && activeActionId === act.id;

          return (
            <button
              key={act.id}
              type="button"
              disabled={isLoading}
              onClick={() => handleClick(act.id, act.condition_id)}
              className={`inline-flex items-center gap-2 h-9 px-3.5 rounded-[6px] text-xs font-medium cursor-pointer transition-all focus-visible:outline-2 focus-visible:outline-[var(--accent-primary)] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${
                isAyu
                  ? 'bg-[var(--bg-elevated)] hover:bg-[#343e49] text-[var(--accent-hover)] border border-[var(--border-subtle)]'
                  : 'bg-[var(--accent-primary)]/15 hover:bg-[var(--accent-primary)]/25 text-[var(--accent-primary)] border border-[var(--accent-primary)]/30 shadow-sm'
              }`}
            >
              {isCurrentLoading ? (
                <Loader2 size={14} className="animate-spin shrink-0" />
              ) : isAyu ? (
                <Leaf size={14} className="shrink-0 text-[var(--accent-hover)]" />
              ) : (
                <Building2 size={14} className="shrink-0 text-[var(--accent-primary)]" />
              )}
              <span>{act.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default CareActionBar;
