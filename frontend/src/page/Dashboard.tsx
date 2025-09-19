import AgentStatus from "../components/dashboard/AgentStatus";
import Card from "../components/dashboard/Card";
import PendingSession from "../components/dashboard/PendingSession";
// import { useState, useEffect } from "react";
import useSWR from "swr";

interface AdminDashboardStats {
  pending_sessions: number;
  active_sessions: number;
  total_agents: number;
  online_agents: number;
  total_users: number;
  today_conversations: number;
}

export default function Dashboard() {
  const { data: stats, isLoading } = useSWR<AdminDashboardStats>(
    "/admin-dashboard/dashboard-stats/"
  );

  if (isLoading) {
    return (
      <div className="pt-4 space-y-5">
        <h2 className="font-bold text-2xl">Admin Dashboard</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-10">
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

  return (
    <div className="pt-4 space-y-5">
      <h2 className="font-bold text-2xl">Admin Dashboard</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6">
        <Card title="Pending Sessions" count={stats?.pending_sessions || 0} />
        <Card title="Active Sessions" count={stats?.active_sessions || 0} />
        <Card title="Total Agents" count={stats?.total_agents || 0} />
        <Card title="Online Agents" count={stats?.online_agents || 0} />
        <Card title="Total Users" count={stats?.total_users || 0} />
        <Card title="Today's Chats" count={stats?.today_conversations || 0} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-[30px]">
        <PendingSession />
        <AgentStatus />
      </div>
    </div>
  );
}
