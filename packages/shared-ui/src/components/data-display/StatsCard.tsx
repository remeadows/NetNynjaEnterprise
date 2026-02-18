import * as React from "react";
import { cn } from "../../utils/cn";

export interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
  loading?: boolean;
}

export function StatsCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  className,
  loading = false,
}: StatsCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-dark-700 bg-[#0f172a] p-4",
        className,
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium uppercase tracking-wider text-silver-500">
            {title}
          </p>
          {loading ? (
            <div className="mt-1 h-6 w-20 animate-pulse rounded bg-dark-700" />
          ) : (
            <p className="mt-1 text-2xl font-semibold text-silver-100">
              {value}
            </p>
          )}
          {subtitle && (
            <p className="mt-0.5 text-xs text-silver-500">{subtitle}</p>
          )}
          {trend && (
            <div className="mt-2 flex items-center gap-1">
              <span
                className={cn(
                  "flex items-center text-sm font-medium",
                  trend.isPositive ? "text-success-400" : "text-error-400",
                )}
              >
                {trend.isPositive ? (
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 10l7-7m0 0l7 7m-7-7v18"
                    />
                  </svg>
                ) : (
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 14l-7 7m0 0l-7-7m7 7V3"
                    />
                  </svg>
                )}
                {Math.abs(trend.value)}%
              </span>
              <span className="text-sm text-silver-500">from last period</span>
            </div>
          )}
        </div>
        {icon && (
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-900/50 text-primary-400 shadow-[0_0_8px_rgba(0,212,255,0.2)]">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
