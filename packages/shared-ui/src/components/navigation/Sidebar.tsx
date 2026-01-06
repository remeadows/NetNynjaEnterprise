import * as React from 'react';
import { cn } from '../../utils/cn';
import { type ModuleType, moduleColors } from '../../theme';

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon?: React.ReactNode;
  badge?: string | number;
  children?: NavItem[];
}

export interface SidebarProps {
  module: ModuleType;
  items: NavItem[];
  currentPath: string;
  onNavigate: (href: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}

export function Sidebar({
  module,
  items,
  currentPath,
  onNavigate,
  collapsed = false,
  onToggleCollapse,
  header,
  footer,
}: SidebarProps) {
  const colors = moduleColors[module];

  return (
    <aside
      className={cn(
        'flex h-full flex-col border-r border-gray-200 bg-white transition-all dark:border-gray-700 dark:bg-gray-900',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {header && (
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4 dark:border-gray-700">
          {header}
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <svg
                className={cn('h-5 w-5 transition-transform', collapsed && 'rotate-180')}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                />
              </svg>
            </button>
          )}
        </div>
      )}

      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
        {items.map((item) => {
          const isActive = currentPath === item.href || currentPath.startsWith(item.href + '/');

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.href)}
              className={cn(
                'flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'text-white'
                  : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
              )}
              style={isActive ? { backgroundColor: colors.primary } : undefined}
            >
              {item.icon && (
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center">
                  {item.icon}
                </span>
              )}
              {!collapsed && (
                <>
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge !== undefined && (
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-xs',
                        isActive
                          ? 'bg-white/20 text-white'
                          : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </button>
          );
        })}
      </nav>

      {footer && (
        <div className="border-t border-gray-200 p-4 dark:border-gray-700">
          {footer}
        </div>
      )}
    </aside>
  );
}
