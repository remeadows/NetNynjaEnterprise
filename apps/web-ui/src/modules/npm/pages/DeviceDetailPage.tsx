import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  StatsCard,
  StatusIndicator,
  LineChart,
} from "@netnynja/shared-ui";
import { useNPMStore } from "../../../stores/npm";

export function NPMDeviceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedDevice, isLoading, fetchDevice, deleteDevice } =
    useNPMStore();

  useEffect(() => {
    if (id) {
      fetchDevice(id);
    }
  }, [id, fetchDevice]);

  const handleDelete = async () => {
    if (id && window.confirm("Are you sure you want to delete this device?")) {
      await deleteDevice(id);
      navigate("/npm/devices");
    }
  };

  const statusMap = {
    up: "success",
    down: "error",
    warning: "warning",
    unknown: "neutral",
  } as const;

  // Sample metrics data
  const metricsData = [
    { time: "00:00", cpu: 45, memory: 62 },
    { time: "04:00", cpu: 38, memory: 58 },
    { time: "08:00", cpu: 72, memory: 75 },
    { time: "12:00", cpu: 65, memory: 70 },
    { time: "16:00", cpu: 58, memory: 68 },
    { time: "20:00", cpu: 42, memory: 60 },
    { time: "24:00", cpu: 35, memory: 55 },
  ];

  if (!selectedDevice && !isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500">Device not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate("/npm/devices")}>
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
          <div className="flex items-center gap-3">
            {selectedDevice && (
              <StatusIndicator
                status={statusMap[selectedDevice.status]}
                size="lg"
                pulse={selectedDevice.status === "down"}
              />
            )}
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {selectedDevice?.name || "Loading..."}
              </h1>
              <p className="text-gray-500 dark:text-gray-400">
                {selectedDevice?.ipAddress}
              </p>
            </div>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="outline">
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Poll Now
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="CPU Utilization"
          value="45%"
          trend={{ value: 5, isPositive: false }}
        />
        <StatsCard
          title="Memory Utilization"
          value="62%"
          trend={{ value: 2, isPositive: true }}
        />
        <StatsCard title="Uptime" value="45d 12h" />
        <StatsCard
          title="Poll Interval"
          value={`${selectedDevice?.pollInterval || 60}s`}
        />
      </div>

      {/* Device Details */}
      <Card>
        <CardHeader>
          <CardTitle>Device Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Device Type
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedDevice?.deviceType || "Unknown"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Vendor
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedDevice?.vendor || "Unknown"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Model
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedDevice?.model || "Unknown"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                SNMP Polling
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedDevice?.pollSnmp ? "SNMPv3 Enabled" : "Disabled"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                SSH Enabled
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedDevice?.sshEnabled ? "Yes" : "No"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Last Poll
              </dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {selectedDevice?.lastPoll
                  ? new Date(selectedDevice.lastPoll).toLocaleString()
                  : "Never"}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Metrics Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Resource Utilization (24h)</CardTitle>
        </CardHeader>
        <CardContent>
          <LineChart
            data={metricsData}
            series={[
              { dataKey: "cpu", name: "CPU %", color: "#3b82f6" },
              { dataKey: "memory", name: "Memory %", color: "#10b981" },
            ]}
            xAxisKey="time"
            height={300}
            yAxisFormatter={(v) => `${v}%`}
          />
        </CardContent>
      </Card>
    </div>
  );
}
