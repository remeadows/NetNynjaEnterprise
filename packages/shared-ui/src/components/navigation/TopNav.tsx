import * as React from 'react';
import { cn } from '../../utils/cn';
import { type ModuleType, moduleColors } from '../../theme';

export interface ModuleTab {
  id: ModuleType;
  label: string;
  href: string;
  icon?: React.ReactNode;
}

export interface TopNavProps {
  modules: ModuleTab[];
  activeModule: ModuleType;
  onModuleChange: (module: ModuleType) => void;
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  onLogout?: () => void;
  onThemeToggle?: () => void;
  isDark?: boolean;
  logo?: React.ReactNode;
}

export function TopNav({
  modules,
  activeModule,
  onModuleChange,
  user,
  onLogout,
  onThemeToggle,
  isDark,
  logo,
}: TopNavProps) {
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 dark:border-gray-700 dark:bg-gray-900">
      <div className="flex items-center gap-8">
        {logo && <div className="flex items-center">{logo}</div>}

        <nav className="flex items-center gap-1">
          {modules.map((mod) => {
            const isActive = activeModule === mod.id;
            const colors = moduleColors[mod.id];

            return (
              <button
                key={mod.id}
                onClick={() => onModuleChange(mod.id)}
                className={cn(
                  'flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'text-white'
                    : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                )}
                style={isActive ? { backgroundColor: colors.primary } : undefined}
              >
                {mod.icon && <span className="h-4 w-4">{mod.icon}</span>}
                {mod.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {onThemeToggle && (
          <button
            onClick={onThemeToggle}
            className="rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            aria-label="Toggle theme"
          >
            {isDark ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
        )}

        {user && (
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 rounded-md p-2 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm font-medium text-white">
                {user.avatar ? (
                  <img src={user.avatar} alt={user.name} className="h-full w-full rounded-full object-cover" />
                ) : (
                  user.name.charAt(0).toUpperCase()
                )}
              </div>
              <span className="hidden text-sm font-medium text-gray-700 dark:text-gray-300 md:block">
                {user.name}
              </span>
              <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 rounded-md border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800">
                <div className="border-b border-gray-200 px-4 py-2 dark:border-gray-700">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{user.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
                </div>
                {onLogout && (
                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      onLogout();
                    }}
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Sign out
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
