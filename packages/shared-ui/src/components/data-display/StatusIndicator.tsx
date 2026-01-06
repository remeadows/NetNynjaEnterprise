import * as React from 'react';
import { cn } from '../../utils/cn';

export type StatusType = 'success' | 'warning' | 'error' | 'info' | 'neutral';

export interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const statusColors: Record<StatusType, string> = {
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  error: 'bg-error-500',
  info: 'bg-info-500',
  neutral: 'bg-gray-400',
};

const sizeClasses = {
  sm: 'h-2 w-2',
  md: 'h-3 w-3',
  lg: 'h-4 w-4',
};

export function StatusIndicator({
  status,
  label,
  pulse = false,
  size = 'md',
}: StatusIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex">
        {pulse && (
          <span
            className={cn(
              'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
              statusColors[status]
            )}
          />
        )}
        <span className={cn('relative inline-flex rounded-full', sizeClasses[size], statusColors[status])} />
      </span>
      {label && (
        <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
      )}
    </div>
  );
}
