import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthTokens } from '@netnynja/shared-types';
import { api } from '../lib/api';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  refreshTokens: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post<{
            data: { user: User; tokens: AuthTokens };
          }>('/api/v1/auth/login', { username, password });

          const { user, tokens } = response.data.data;
          set({
            user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({ error: message, isLoading: false });
          throw err;
        }
      },

      logout: async () => {
        try {
          const { tokens } = get();
          if (tokens?.refreshToken) {
            await api.post('/api/v1/auth/logout', {
              refreshToken: tokens.refreshToken,
            });
          }
        } catch {
          // Ignore logout errors
        } finally {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
          });
        }
      },

      checkAuth: async () => {
        const { tokens } = get();
        if (!tokens?.accessToken) {
          set({ isAuthenticated: false });
          return;
        }

        try {
          const response = await api.get<{ data: { user: User } }>(
            '/api/v1/auth/me'
          );
          set({ user: response.data.data.user, isAuthenticated: true });
        } catch {
          // Token expired or invalid
          const { refreshTokens, logout } = get();
          try {
            await refreshTokens();
          } catch {
            await logout();
          }
        }
      },

      refreshTokens: async () => {
        const { tokens } = get();
        if (!tokens?.refreshToken) {
          throw new Error('No refresh token');
        }

        try {
          const response = await api.post<{
            data: { tokens: AuthTokens };
          }>('/api/v1/auth/refresh', {
            refreshToken: tokens.refreshToken,
          });

          set({
            tokens: response.data.data.tokens,
            isAuthenticated: true,
          });
        } catch (err) {
          set({ tokens: null, isAuthenticated: false });
          throw err;
        }
      },
    }),
    {
      name: 'netnynja-auth',
      partialize: (state) => ({
        tokens: state.tokens,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
