// src/components/ui/RiskBadge.jsx
import React from 'react';
import { cn } from '../../utils/cn';

const RiskBadge = ({ level = 'not_assessed', confidence, className = '' }) => {
  const normalizedLevel = (level || 'not_assessed').toLowerCase();
  if (normalizedLevel === 'not_assessed') {
    return null;
  }

  const config = {
    low: {
      bg: 'bg-[var(--severity-routine)]/15',
      border: 'border-[var(--severity-routine)]/30',
      text: 'text-[var(--severity-routine)]',
      label: 'LOW RISK · ROUTINE',
      dot: 'bg-[var(--severity-routine)]',
    },
    routine: {
      bg: 'bg-[var(--severity-routine)]/15',
      border: 'border-[var(--severity-routine)]/30',
      text: 'text-[var(--severity-routine)]',
      label: 'ROUTINE CARE',
      dot: 'bg-[var(--severity-routine)]',
    },
    self_care: {
      bg: 'bg-[var(--severity-selfcare)]/15',
      border: 'border-[var(--severity-selfcare)]/30',
      text: 'text-[var(--severity-selfcare)]',
      label: 'SELF CARE / MONITOR',
      dot: 'bg-[var(--severity-selfcare)]',
    },
    medium: {
      bg: 'bg-[var(--severity-urgent)]/15',
      border: 'border-[var(--severity-urgent)]/30',
      text: 'text-[var(--severity-urgent)]',
      label: 'MEDIUM RISK · URGENT',
      dot: 'bg-[var(--severity-urgent)]',
    },
    urgent: {
      bg: 'bg-[var(--severity-urgent)]/15',
      border: 'border-[var(--severity-urgent)]/30',
      text: 'text-[var(--severity-urgent)]',
      label: 'URGENT · 24H EVALUATION',
      dot: 'bg-[var(--severity-urgent)]',
    },
    high: {
      bg: 'bg-[var(--severity-emergency)]/15',
      border: 'border-[var(--severity-emergency)]/30',
      text: 'text-[var(--severity-emergency)]',
      label: 'HIGH RISK · IMMEDIATE CARE',
      dot: 'bg-[var(--severity-emergency)] animate-pulse',
    },
    emergency: {
      bg: 'bg-[var(--severity-emergency)]/20',
      border: 'border-[var(--severity-emergency)]/40',
      text: 'text-[var(--severity-emergency)]',
      label: 'EMERGENCY · DIAL 108',
      dot: 'bg-[var(--severity-emergency)] animate-pulse',
    },
  };

  const style = config[normalizedLevel] || config.low;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[6px] border text-[11px] font-mono tracking-tight font-medium select-none shadow-sm',
        style.bg,
        style.border,
        style.text,
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', style.dot)} />
      <span>{style.label}</span>
    </div>
  );
};

export default RiskBadge;
