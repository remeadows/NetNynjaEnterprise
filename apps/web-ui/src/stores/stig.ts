import { create } from 'zustand';
import type {
  Target,
  STIGDefinition,
  AuditJob,
  ComplianceSummary,
  STIGDashboard,
} from '@netnynja/shared-types';
import { api } from '../lib/api';

interface STIGState {
  targets: Target[];
  selectedTarget: Target | null;
  benchmarks: STIGDefinition[];
  auditJobs: AuditJob[];
  complianceSummary: ComplianceSummary | null;
  dashboard: STIGDashboard | null;
  isLoading: boolean;
  error: string | null;

  fetchTargets: () => Promise<void>;
  fetchTarget: (id: string) => Promise<void>;
  fetchBenchmarks: () => Promise<void>;
  createTarget: (data: Partial<Target>) => Promise<Target>;
  deleteTarget: (id: string) => Promise<void>;
  startAudit: (targetId: string, definitionId: string) => Promise<AuditJob>;
  fetchComplianceSummary: () => Promise<void>;
  fetchDashboard: () => Promise<void>;
}

export const useSTIGStore = create<STIGState>((set) => ({
  targets: [],
  selectedTarget: null,
  benchmarks: [],
  auditJobs: [],
  complianceSummary: null,
  dashboard: null,
  isLoading: false,
  error: null,

  fetchTargets: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: Target[] }>('/api/v1/stig/assets');
      set({ targets: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch targets';
      set({ error: message, isLoading: false });
    }
  },

  fetchTarget: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: Target }>(`/api/v1/stig/assets/${id}`);
      set({ selectedTarget: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch target';
      set({ error: message, isLoading: false });
    }
  },

  fetchBenchmarks: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: STIGDefinition[] }>('/api/v1/stig/benchmarks');
      set({ benchmarks: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch benchmarks';
      set({ error: message, isLoading: false });
    }
  },

  createTarget: async (data: Partial<Target>) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<{ data: Target }>('/api/v1/stig/assets', data);
      const target = response.data.data;
      set((state) => ({
        targets: [...state.targets, target],
        isLoading: false,
      }));
      return target;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create target';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  deleteTarget: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/api/v1/stig/assets/${id}`);
      set((state) => ({
        targets: state.targets.filter((t) => t.id !== id),
        selectedTarget: state.selectedTarget?.id === id ? null : state.selectedTarget,
        isLoading: false,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete target';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  startAudit: async (targetId: string, definitionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<{ data: AuditJob }>('/api/v1/stig/audits', {
        targetId,
        definitionId,
      });
      const auditJob = response.data.data;
      set((state) => ({
        auditJobs: [...state.auditJobs, auditJob],
        isLoading: false,
      }));
      return auditJob;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start audit';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  fetchComplianceSummary: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: ComplianceSummary }>(
        '/api/v1/stig/compliance/summary'
      );
      set({ complianceSummary: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch compliance summary';
      set({ error: message, isLoading: false });
    }
  },

  fetchDashboard: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: STIGDashboard }>('/api/v1/stig/dashboard');
      set({ dashboard: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch dashboard';
      set({ error: message, isLoading: false });
    }
  },
}));
