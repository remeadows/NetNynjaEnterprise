import { create } from "zustand";
import type { Device, Alert, NPMDashboard } from "@netnynja/shared-types";
import { api } from "../lib/api";

export interface CreateDeviceInput {
  name: string;
  ipAddress: string;
  deviceType?: string;
  vendor?: string;
  model?: string;
  pollIcmp?: boolean;
  pollSnmp?: boolean;
  snmpv3CredentialId?: string;
  snmpPort?: number;
  sshEnabled?: boolean;
  pollInterval?: number;
  isActive?: boolean;
}

export interface UpdateDeviceInput {
  name?: string;
  ipAddress?: string;
  deviceType?: string;
  vendor?: string;
  model?: string;
  pollIcmp?: boolean;
  pollSnmp?: boolean;
  snmpv3CredentialId?: string | null;
  snmpPort?: number;
  sshEnabled?: boolean;
  pollInterval?: number;
  isActive?: boolean;
}

interface NPMState {
  devices: Device[];
  selectedDevice: Device | null;
  alerts: Alert[];
  dashboard: NPMDashboard | null;
  isLoading: boolean;
  error: string | null;

  fetchDevices: () => Promise<void>;
  fetchDevice: (id: string) => Promise<void>;
  fetchAlerts: () => Promise<void>;
  createDevice: (data: CreateDeviceInput) => Promise<Device>;
  updateDevice: (id: string, data: UpdateDeviceInput) => Promise<Device>;
  deleteDevice: (id: string) => Promise<void>;
  acknowledgeAlert: (alertId: string) => Promise<void>;
  fetchDashboard: () => Promise<void>;
}

export const useNPMStore = create<NPMState>((set) => ({
  devices: [],
  selectedDevice: null,
  alerts: [],
  dashboard: null,
  isLoading: false,
  error: null,

  fetchDevices: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: Device[] }>("/api/v1/npm/devices");
      set({ devices: response.data.data, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch devices";
      set({ error: message, isLoading: false });
    }
  },

  fetchDevice: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: Device }>(
        `/api/v1/npm/devices/${id}`,
      );
      set({ selectedDevice: response.data.data, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch device";
      set({ error: message, isLoading: false });
    }
  },

  fetchAlerts: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: Alert[] }>("/api/v1/npm/alerts");
      set({ alerts: response.data.data, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch alerts";
      set({ error: message, isLoading: false });
    }
  },

  createDevice: async (data: CreateDeviceInput) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<{ data: Device }>(
        "/api/v1/npm/devices",
        data,
      );
      const device = response.data.data;
      set((state) => ({
        devices: [...state.devices, device],
        isLoading: false,
      }));
      return device;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create device";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  updateDevice: async (id: string, data: UpdateDeviceInput) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.patch<{ data: Device }>(
        `/api/v1/npm/devices/${id}`,
        data,
      );
      const device = response.data.data;
      set((state) => ({
        devices: state.devices.map((d) => (d.id === id ? device : d)),
        selectedDevice:
          state.selectedDevice?.id === id ? device : state.selectedDevice,
        isLoading: false,
      }));
      return device;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to update device";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  deleteDevice: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/api/v1/npm/devices/${id}`);
      set((state) => ({
        devices: state.devices.filter((d) => d.id !== id),
        selectedDevice:
          state.selectedDevice?.id === id ? null : state.selectedDevice,
        isLoading: false,
      }));
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to delete device";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  acknowledgeAlert: async (alertId: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.post(`/api/v1/npm/alerts/${alertId}/acknowledge`);
      set((state) => ({
        alerts: state.alerts.map((a) =>
          a.id === alertId
            ? {
                ...a,
                status: "acknowledged" as const,
                acknowledgedAt: new Date(),
              }
            : a,
        ),
        isLoading: false,
      }));
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to acknowledge alert";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  fetchDashboard: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ data: NPMDashboard }>(
        "/api/v1/npm/dashboard",
      );
      set({ dashboard: response.data.data, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch dashboard";
      set({ error: message, isLoading: false });
    }
  },
}));
