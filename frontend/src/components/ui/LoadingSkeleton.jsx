// src/components/ui/LoadingSkeleton.jsx
import React from 'react';
import Card from '../common/Card';

export const CardSkeleton = () => {
  return (
    <Card className="space-y-3 animate-pulse">
      <div className="h-4 bg-[var(--bg-elevated)] rounded-[4px] w-1/3" />
      <div className="h-7 bg-[var(--bg-elevated)] rounded-[6px] w-2/3" />
      <div className="h-3 bg-[var(--bg-elevated)] rounded-[4px] w-1/2" />
    </Card>
  );
};

export const TableSkeleton = ({ rows = 3 }) => {
  return (
    <div className="space-y-2.5 animate-pulse">
      {Array.from({ length: rows }).map((_, idx) => (
        <div
          key={idx}
          className="h-14 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[8px] p-3 flex items-center justify-between"
        >
          <div className="h-4 bg-[var(--bg-elevated)] rounded-[4px] w-1/4" />
          <div className="h-4 bg-[var(--bg-elevated)] rounded-[4px] w-1/3" />
          <div className="h-5 bg-[var(--bg-elevated)] rounded-[4px] w-16" />
        </div>
      ))}
    </div>
  );
};

export default CardSkeleton;
