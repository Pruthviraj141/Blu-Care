// src/components/ui/Toast.jsx
import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { cn } from '../../utils/cn';

const Toast = ({ id, type = 'info', message, onClose }) => {
  const styles = {
    info: {
      border: 'border-[var(--clinical-teal)]/40',
      icon: Info,
      iconColor: 'text-[var(--clinical-teal)]',
    },
    success: {
      border: 'border-[var(--severity-routine)]/40',
      icon: CheckCircle2,
      iconColor: 'text-[var(--severity-routine)]',
    },
    warning: {
      border: 'border-[var(--severity-urgent)]/40',
      icon: AlertTriangle,
      iconColor: 'text-[var(--severity-urgent)]',
    },
    error: {
      border: 'border-[var(--severity-emergency)]/40',
      icon: AlertCircle,
      iconColor: 'text-[var(--severity-emergency)]',
    },
  };

  const config = styles[type] || styles.info;
  const IconComponent = config.icon;

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-[8px] border bg-[var(--bg-elevated)] shadow-lg text-xs text-[var(--text-primary)] transition-all duration-200 animate-fade-in',
        config.border
      )}
    >
      <div className="flex items-center gap-2.5 min-w-0">
        <IconComponent size={16} className={cn('shrink-0', config.iconColor)} />
        <span className="font-medium truncate">{message}</span>
      </div>
      <button
        type="button"
        onClick={() => onClose(id)}
        className="p-1 rounded-[4px] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)] transition-colors cursor-pointer"
        aria-label="Dismiss toast"
      >
        <X size={14} />
      </button>
    </div>
  );
};

export default Toast;
