import MyActiveSession from "../../components/agent/MyActiveSession";
import PendingSession from "../../components/agent/PendingSession";
import Card from "../../components/dashboard/Card";
import { useAgentRealTimeData } from "../../hooks/useAgentWebSocket";

interface AgentDashboardStats {
  pending_sessions: number;
  my_active_sessions: number;
  total_handled_today: number;
  total_handled_all_time: number;
  agent_status: "AVAILABLE" | "BUSY" | "OFFLINE";
}

export default function Dashboard() {
  const { stats, isConnected, statsLoading } = useAgentRealTimeData();

  if (statsLoading) {
    return (
      <div className="pt-4 space-y-5">
        <h2 className="font-bold text-2xl">Agent Dashboard</h2>
        <div className="grid grid-cols-2 md:grid-cols-2 xl:grid-cols-4 gap-10">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-white p-6 rounded-lg shadow-sm border animate-pulse"
            >
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "AVAILABLE":
        return "text-green-600";
      case "BUSY":
        return "text-yellow-600";
      case "OFFLINE":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="pt-4 space-y-5">
      <div className="flex justify-between items-center">
        <h2 className="font-bold text-2xl">Agent Dashboard</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">Status:</span>
          <span
            className={`font-semibold ${getStatusColor(
              stats?.agent_status || "OFFLINE"
            )}`}
          >
            {stats?.agent_status || "OFFLINE"}
          </span>
          {/* WebSocket connection indicator */}
          <span
            className={`text-xs px-2 py-1 rounded ${
              isConnected
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {isConnected ? "🟢 Live Updates" : "🔴 No Live Updates"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <Card title="Pending Sessions" count={stats?.pending_sessions || 0} />
        <Card
          title="My Active Sessions"
          count={stats?.my_active_sessions || 0}
        />
        <Card title="Handled Today" count={stats?.total_handled_today || 0} />
        <Card
          title="Total Handled"
          count={stats?.total_handled_all_time || 0}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <PendingSession />
        <MyActiveSession />
      </div>
    </div>
  );
}
