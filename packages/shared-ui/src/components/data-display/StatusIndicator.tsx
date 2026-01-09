import * as React from "react";
import { cn } from "../../utils/cn";

export type StatusType = "success" | "warning" | "error" | "info" | "neutral";

export interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  pulse?: boolean;
  size?: "sm" | "md" | "lg";
}

const statusColors: Record<StatusType, string> = {
  success: "bg-green-500",
  warning: "bg-yellow-500",
  error: "bg-red-500",
  info: "bg-blue-500",
  neutral: "bg-gray-400 dark:bg-gray-500",
};

const statusTextColors: Record<StatusType, string> = {
  success: "text-green-700 dark:text-green-400",
  warning: "text-yellow-700 dark:text-yellow-400",
  error: "text-red-700 dark:text-red-400",
  info: "text-blue-700 dark:text-blue-400",
  neutral: "text-gray-600 dark:text-gray-300",
};

const sizeClasses = {
  sm: "h-2 w-2",
  md: "h-3 w-3",
  lg: "h-4 w-4",
};

export function StatusIndicator({
  status,
  label,
  pulse = false,
  size = "md",
}: StatusIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex">
        {pulse && (
          <span
            className={cn(
              "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
              statusColors[status],
            )}
          />
        )}
        <span
          className={cn(
            "relative inline-flex rounded-full",
            sizeClasses[size],
            statusColors[status],
          )}
        />
      </span>
      {label && (
        <span className={cn("text-sm font-medium", statusTextColors[status])}>
          {label}
        </span>
      )}
    </div>
  );
}
