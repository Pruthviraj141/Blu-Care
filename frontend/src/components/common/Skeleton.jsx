// src/components/common/Skeleton.jsx
import React from 'react';
import { cn } from '../../utils/cn';

/**
 * Shimmer Loading Skeleton
 */
const Skeleton = ({
  className = '',
  width,
  height,
  rounded = 'rounded-[6px]',
  ...props
}) => {
  return (
    <div
      className={cn(
        'animate-pulse bg-[var(--bg-elevated)]/70',
        rounded,
        className
      )}
      style={{
        width,
        height,
      }}
      {...props}
    />
  );
};

export default Skeleton;

