import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  DataTable,
  Badge,
  Input,
} from "@netnynja/shared-ui";
import type { ColumnDef } from "@tanstack/react-table";
import type { Network } from "@netnynja/shared-types";
import { useIPAMStore } from "../../../stores/ipam";

const columns: ColumnDef<Network>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => (
      <span className="font-medium text-gray-900 dark:text-white">
        {row.original.name}
      </span>
    ),
  },
  {
    accessorKey: "network",
    header: "Network",
    cell: ({ row }) => (
      <code className="rounded bg-gray-100 px-2 py-1 text-sm dark:bg-gray-800">
        {row.original.network}
      </code>
    ),
  },
  {
    accessorKey: "vlanId",
    header: "VLAN",
    cell: ({ row }) => row.original.vlanId || "-",
  },
  {
    accessorKey: "site",
    header: "Site",
    cell: ({ row }) => row.original.site || "-",
  },
  {
    accessorKey: "location",
    header: "Location",
    cell: ({ row }) => row.original.location || "-",
  },
  {
    accessorKey: "isActive",
    header: "Status",
    cell: ({ row }) => (
      <Badge variant={row.original.isActive ? "success" : "secondary"}>
        {row.original.isActive ? "Active" : "Inactive"}
      </Badge>
    ),
  },
];

export function IPAMNetworksPage() {
  const navigate = useNavigate();
  const { networks, isLoading, fetchNetworks, createNetwork } = useIPAMStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newNetwork, setNewNetwork] = useState({
    name: "",
    network: "",
    vlanId: "",
    site: "",
    location: "",
    description: "",
    isActive: true,
  });

  useEffect(() => {
    fetchNetworks();
  }, [fetchNetworks]);

  const handleAddNetwork = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createNetwork({
        name: newNetwork.name,
        network: newNetwork.network,
        vlanId: newNetwork.vlanId ? parseInt(newNetwork.vlanId) : undefined,
        site: newNetwork.site || undefined,
        location: newNetwork.location || undefined,
        description: newNetwork.description || undefined,
        isActive: newNetwork.isActive,
      });
      setShowAddModal(false);
      setNewNetwork({
        name: "",
        network: "",
        vlanId: "",
        site: "",
        location: "",
        description: "",
        isActive: true,
      });
    } catch {
      // Error handled in store
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Networks
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Manage your IP network ranges
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
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
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Network
        </Button>
      </div>

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={networks}
            loading={isLoading}
            searchable
            searchPlaceholder="Search networks..."
            onRowClick={(network) => navigate(`/ipam/networks/${network.id}`)}
            emptyMessage="No networks found. Add your first network to get started."
          />
        </CardContent>
      </Card>

      {/* Add Network Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Network</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddNetwork} className="space-y-4">
                <Input
                  label="Name"
                  value={newNetwork.name}
                  onChange={(e) =>
                    setNewNetwork({ ...newNetwork, name: e.target.value })
                  }
                  placeholder="e.g., Production LAN"
                  required
                />
                <Input
                  label="Network (CIDR)"
                  value={newNetwork.network}
                  onChange={(e) =>
                    setNewNetwork({ ...newNetwork, network: e.target.value })
                  }
                  placeholder="e.g., 192.168.1.0/24"
                  required
                />
                <Input
                  label="VLAN ID"
                  type="number"
                  value={newNetwork.vlanId}
                  onChange={(e) =>
                    setNewNetwork({ ...newNetwork, vlanId: e.target.value })
                  }
                  placeholder="e.g., 100"
                />
                <Input
                  label="Site"
                  value={newNetwork.site}
                  onChange={(e) =>
                    setNewNetwork({ ...newNetwork, site: e.target.value })
                  }
                  placeholder="e.g., Headquarters"
                />
                <Input
                  label="Location"
                  value={newNetwork.location}
                  onChange={(e) =>
                    setNewNetwork({ ...newNetwork, location: e.target.value })
                  }
                  placeholder="e.g., Data Center 1"
                />
                <Input
                  label="Description"
                  value={newNetwork.description}
                  onChange={(e) =>
                    setNewNetwork({
                      ...newNetwork,
                      description: e.target.value,
                    })
                  }
                  placeholder="Optional description"
                />
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="isActive"
                    checked={newNetwork.isActive}
                    onChange={(e) =>
                      setNewNetwork({
                        ...newNetwork,
                        isActive: e.target.checked,
                      })
                    }
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <label
                    htmlFor="isActive"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Active
                  </label>
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowAddModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" loading={isLoading}>
                    Add Network
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
