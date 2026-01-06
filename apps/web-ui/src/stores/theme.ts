import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ModuleType } from '@netnynja/shared-ui';

interface ThemeState {
  isDark: boolean;
  activeModule: ModuleType;
  sidebarCollapsed: boolean;
  toggleTheme: () => void;
  setActiveModule: (module: ModuleType) => void;
  toggleSidebar: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      isDark: false,
      activeModule: 'ipam',
      sidebarCollapsed: false,

      toggleTheme: () => {
        set((state) => ({ isDark: !state.isDark }));
      },

      setActiveModule: (module: ModuleType) => {
        set({ activeModule: module });
      },

      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },
    }),
    {
      name: 'netnynja-theme',
    }
  )
);
