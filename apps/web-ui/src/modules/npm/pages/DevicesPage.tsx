import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, CardContent, DataTable, Input, Select, StatusIndicator } from '@netnynja/shared-ui';
import type { ColumnDef } from '@tanstack/react-table';
import type { Device } from '@netnynja/shared-types';
import { useNPMStore } from '../../../stores/npm';

const statusMap = {
  up: 'success',
  down: 'error',
  warning: 'warning',
  unknown: 'neutral',
} as const;

const columns: ColumnDef<Device>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => (
      <span className="font-medium text-gray-900 dark:text-white">{row.original.name}</span>
    ),
  },
  {
    accessorKey: 'ipAddress',
    header: 'IP Address',
    cell: ({ row }) => (
      <code className="rounded bg-gray-100 px-2 py-1 text-sm dark:bg-gray-800">
        {row.original.ipAddress}
      </code>
    ),
  },
  {
    accessorKey: 'deviceType',
    header: 'Type',
    cell: ({ row }) => row.original.deviceType || '-',
  },
  {
    accessorKey: 'vendor',
    header: 'Vendor',
    cell: ({ row }) => row.original.vendor || '-',
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => (
      <StatusIndicator
        status={statusMap[row.original.status]}
        label={row.original.status.toUpperCase()}
        pulse={row.original.status === 'down'}
      />
    ),
  },
  {
    accessorKey: 'lastPoll',
    header: 'Last Poll',
    cell: ({ row }) =>
      row.original.lastPoll
        ? new Date(row.original.lastPoll).toLocaleString()
        : 'Never',
  },
];

export function NPMDevicesPage() {
  const navigate = useNavigate();
  const { devices, isLoading, fetchDevices, createDevice } = useNPMStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newDevice, setNewDevice] = useState({
    name: '',
    ipAddress: '',
    deviceType: '',
    vendor: '',
    snmpVersion: 'v2c',
    pollInterval: '60',
  });

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const handleAddDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createDevice({
        name: newDevice.name,
        ipAddress: newDevice.ipAddress,
        deviceType: newDevice.deviceType || undefined,
        vendor: newDevice.vendor || undefined,
        snmpVersion: newDevice.snmpVersion as 'v1' | 'v2c' | 'v3',
        pollInterval: parseInt(newDevice.pollInterval),
        isActive: true,
        sshEnabled: false,
      });
      setShowAddModal(false);
      setNewDevice({
        name: '',
        ipAddress: '',
        deviceType: '',
        vendor: '',
        snmpVersion: 'v2c',
        pollInterval: '60',
      });
    } catch {
      // Error handled in store
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Devices</h1>
          <p className="text-gray-500 dark:text-gray-400">Monitor your network devices</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Device
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <StatusIndicator status="success" size="lg" />
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {devices.filter((d) => d.status === 'up').length}
              </p>
              <p className="text-sm text-gray-500">Devices Up</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <StatusIndicator status="error" size="lg" pulse />
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {devices.filter((d) => d.status === 'down').length}
              </p>
              <p className="text-sm text-gray-500">Devices Down</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <StatusIndicator status="warning" size="lg" />
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {devices.filter((d) => d.status === 'warning').length}
              </p>
              <p className="text-sm text-gray-500">Warnings</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <StatusIndicator status="neutral" size="lg" />
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{devices.length}</p>
              <p className="text-sm text-gray-500">Total Devices</p>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={devices}
            loading={isLoading}
            searchable
            searchPlaceholder="Search devices..."
            onRowClick={(device) => navigate(`/npm/devices/${device.id}`)}
            emptyMessage="No devices found. Add your first device to start monitoring."
          />
        </CardContent>
      </Card>

      {/* Add Device Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <CardContent className="pt-6">
              <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Add Device</h2>
              <form onSubmit={handleAddDevice} className="space-y-4">
                <Input
                  label="Name"
                  value={newDevice.name}
                  onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
                  placeholder="e.g., Core Router 1"
                  required
                />
                <Input
                  label="IP Address"
                  value={newDevice.ipAddress}
                  onChange={(e) => setNewDevice({ ...newDevice, ipAddress: e.target.value })}
                  placeholder="e.g., 192.168.1.1"
                  required
                />
                <Input
                  label="Device Type"
                  value={newDevice.deviceType}
                  onChange={(e) => setNewDevice({ ...newDevice, deviceType: e.target.value })}
                  placeholder="e.g., Router, Switch"
                />
                <Input
                  label="Vendor"
                  value={newDevice.vendor}
                  onChange={(e) => setNewDevice({ ...newDevice, vendor: e.target.value })}
                  placeholder="e.g., Cisco, Juniper"
                />
                <Select
                  label="SNMP Version"
                  value={newDevice.snmpVersion}
                  onChange={(e) => setNewDevice({ ...newDevice, snmpVersion: e.target.value })}
                  options={[
                    { value: 'v1', label: 'SNMP v1' },
                    { value: 'v2c', label: 'SNMP v2c' },
                    { value: 'v3', label: 'SNMP v3' },
                  ]}
                />
                <Input
                  label="Poll Interval (seconds)"
                  type="number"
                  value={newDevice.pollInterval}
                  onChange={(e) => setNewDevice({ ...newDevice, pollInterval: e.target.value })}
                  placeholder="60"
                />
                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => setShowAddModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" loading={isLoading}>
                    Add Device
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
