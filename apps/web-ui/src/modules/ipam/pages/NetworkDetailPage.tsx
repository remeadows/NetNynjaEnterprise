import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  DataTable,
  StatsCard,
  StatusIndicator,
} from "@netnynja/shared-ui";
import type { ColumnDef } from "@tanstack/react-table";
import type { IPAddress } from "@netnynja/shared-types";
import { useIPAMStore } from "../../../stores/ipam";

const columns: ColumnDef<IPAddress>[] = [
  {
    accessorKey: "address",
    header: "IP Address",
    cell: ({ row }) => (
      <code className="rounded bg-gray-100 px-2 py-1 text-sm dark:bg-gray-800">
        {row.original.address}
      </code>
    ),
  },
  {
    accessorKey: "hostname",
    header: "Hostname",
    cell: ({ row }) => row.original.hostname || "-",
  },
  {
    accessorKey: "macAddress",
    header: "MAC Address",
    cell: ({ row }) =>
      row.original.macAddress ? (
        <code className="text-sm">{row.original.macAddress}</code>
      ) : (
        "-"
      ),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const statusMap = {
        active: "success",
        inactive: "neutral",
        reserved: "info",
        dhcp: "warning",
        unknown: "neutral",
      } as const;
      return (
        <StatusIndicator
          status={statusMap[row.original.status]}
          label={
            row.original.status.charAt(0).toUpperCase() +
            row.original.status.slice(1)
          }
        />
      );
    },
  },
  {
    accessorKey: "lastSeen",
    header: "Last Seen",
    cell: ({ row }) =>
      row.original.lastSeen
        ? new Date(row.original.lastSeen).toLocaleDateString()
        : "-",
  },
];

export function IPAMNetworkDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    selectedNetwork,
    addresses,
    isLoading,
    fetchNetwork,
    fetchAddresses,
    startScan,
    deleteNetwork,
  } = useIPAMStore();

  useEffect(() => {
    if (id) {
      fetchNetwork(id);
      fetchAddresses(id);
    }
  }, [id, fetchNetwork, fetchAddresses]);

  const handleScan = async () => {
    if (id) {
      await startScan(id, "ping");
    }
  };

  const handleDelete = async () => {
    if (id && window.confirm("Are you sure you want to delete this network?")) {
      await deleteNetwork(id);
      navigate("/ipam/networks");
    }
  };

  if (!selectedNetwork && !isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500">Network not found</p>
      </div>
    );
  }

  const activeIPs = addresses.filter((a) => a.status === "active").length;
  const totalCapacity = 254; // Assuming /24 for simplicity

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate("/ipam/networks")}>
            <svg
              className="mr-2 h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {selectedNetwork?.name || "Loading..."}
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              {selectedNetwork?.network}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleScan}>
            <svg
              className="mr-2 h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            Scan Network
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Addresses"
          value={addresses.length}
          subtitle={`of ${totalCapacity} available`}
        />
        <StatsCard
          title="Active Devices"
          value={activeIPs}
          icon={
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          }
        />
        <StatsCard
          title="Utilization"
          value={`${Math.round((activeIPs / totalCapacity) * 100)}%`}
        />
        <StatsCard title="VLAN" value={selectedNetwork?.vlanId || "N/A"} />
      </div>

      {/* Network Details */}
      <Card>
        <CardHeader>
          <CardTitle>Network Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Gateway
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedNetwork?.gateway || "Not configured"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Site
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedNetwork?.site || "Not specified"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Location
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedNetwork?.location || "Not specified"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Status
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedNetwork?.isActive ? "Active" : "Inactive"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                DNS Servers
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedNetwork?.dnsServers?.join(", ") || "Not configured"}
              </dd>
            </div>
            <div className="sm:col-span-2 lg:col-span-3">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Description
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedNetwork?.description || "No description"}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* IP Addresses */}
      <Card>
        <CardHeader>
          <CardTitle>IP Addresses</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={addresses}
            loading={isLoading}
            searchable
            searchPlaceholder="Search IP addresses..."
            emptyMessage="No IP addresses discovered yet. Run a network scan to discover devices."
          />
        </CardContent>
      </Card>
    </div>
  );
}
