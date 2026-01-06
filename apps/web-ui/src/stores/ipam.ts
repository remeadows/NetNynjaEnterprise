import { create } from 'zustand';
import type { Network, IPAddress, ScanJob, IPAMDashboard } from '@netnynja/shared-types';
import { api } from '../lib/api';

interface IPAMState {
  networks: Network[];
  selectedNetwork: Network | null;
  addresses: IPAddress[];
  scanJobs: ScanJob[];
  dashboard: IPAMDashboard | null;
  isLoading: boolean;
  error: string | null;

  fetchNetworks: () => Promise<void>;
  fetchNetwork: (id: string) => Promise<void>;
  fetchAddresses: (networkId: string) => Promise<void>;
  createNetwork: (data: Partial<Network>) => Promise<Network>;
  updateNetwork: (id: string, data: Partial<Network>) => Promise<Network>;
  deleteNetwork: (id: string) => Promise<void>;
  startScan: (networkId: string, scanType: string) => Promise<ScanJob>;
  fetchDashboard: () => Promise<void>;
}

export const useIPAMStore = create<IPAMState>((set) => ({
  networks: [],
  selectedNetwork: null,
  addresses: [],
  scanJobs: [],
  dashboard: null,
  isLoading: false,
  error: null,

  fetchNetworks: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: Network[] }>('/api/v1/ipam/networks');
      set({ networks: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch networks';
      set({ error: message, isLoading: false });
    }
  },

  fetchNetwork: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: Network }>(`/api/v1/ipam/networks/${id}`);
      set({ selectedNetwork: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch network';
      set({ error: message, isLoading: false });
    }
  },

  fetchAddresses: async (networkId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: IPAddress[] }>(
        `/api/v1/ipam/networks/${networkId}/addresses`
      );
      set({ addresses: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch addresses';
      set({ error: message, isLoading: false });
    }
  },

  createNetwork: async (data: Partial<Network>) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<{ data: Network }>('/api/v1/ipam/networks', data);
      const network = response.data.data;
      set((state) => ({
        networks: [...state.networks, network],
        isLoading: false,
      }));
      return network;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create network';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  updateNetwork: async (id: string, data: Partial<Network>) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.put<{ data: Network }>(`/api/v1/ipam/networks/${id}`, data);
      const network = response.data.data;
      set((state) => ({
        networks: state.networks.map((n) => (n.id === id ? network : n)),
        selectedNetwork: state.selectedNetwork?.id === id ? network : state.selectedNetwork,
        isLoading: false,
      }));
      return network;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update network';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  deleteNetwork: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/api/v1/ipam/networks/${id}`);
      set((state) => ({
        networks: state.networks.filter((n) => n.id !== id),
        selectedNetwork: state.selectedNetwork?.id === id ? null : state.selectedNetwork,
        isLoading: false,
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete network';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  startScan: async (networkId: string, scanType: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<{ data: ScanJob }>(`/api/v1/ipam/networks/${networkId}/scan`, {
        scanType,
      });
      const scanJob = response.data.data;
      set((state) => ({
        scanJobs: [...state.scanJobs, scanJob],
        isLoading: false,
      }));
      return scanJob;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start scan';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  fetchDashboard: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: IPAMDashboard }>('/api/v1/ipam/dashboard');
      set({ dashboard: response.data.data, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch dashboard';
      set({ error: message, isLoading: false });
    }
  },
}));
