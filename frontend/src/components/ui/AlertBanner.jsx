// src/components/ui/AlertBanner.jsx
import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2, Info } from 'lucide-react';
import { cn } from '../../utils/cn';

const AlertBanner = ({ type = 'info', title, message, actionText, onAction, className = '' }) => {
  const styles = {
    info: {
      bg: 'bg-[var(--severity-info)]/10',
      border: 'border-[var(--severity-info)]/30',
      text: 'text-[var(--severity-info)]',
      icon: Info,
    },
    warning: {
      bg: 'bg-[var(--severity-warning)]/10',
      border: 'border-[var(--severity-warning)]/30',
      text: 'text-[var(--severity-warning)]',
      icon: AlertTriangle,
    },
    danger: {
      bg: 'bg-[var(--severity-emergency)]/10',
      border: 'border-[var(--severity-emergency)]/30',
      text: 'text-[var(--severity-emergency)]',
      icon: AlertCircle,
    },
    success: {
      bg: 'bg-[var(--severity-routine)]/10',
      border: 'border-[var(--severity-routine)]/30',
      text: 'text-[var(--severity-routine)]',
      icon: CheckCircle2,
    },
  };

  const currentStyle = styles[type] || styles.info;
  const IconComponent = currentStyle.icon;

  return (
    <div
      className={cn(
        'p-3.5 sm:p-4 rounded-[8px] border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs',
        currentStyle.bg,
        currentStyle.border,
        className
      )}
    >
      <div className="flex items-start sm:items-center gap-2.5 min-w-0">
        <IconComponent size={18} className={cn('shrink-0 mt-0.5 sm:mt-0', currentStyle.text)} />
        <div className="min-w-0">
          {title && <p className="font-semibold text-[var(--text-primary)] tracking-tight">{title}</p>}
          <p className="text-[var(--text-secondary)] leading-relaxed">{message}</p>
        </div>
      </div>

      {actionText && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="px-3 py-1 rounded-[6px] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--border-strong)] font-medium text-xs transition-colors shrink-0 cursor-pointer"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export default AlertBanner;
