import Card from "../../components/dashboard/Card";
import PlanUpgradeRequests from "../../components/super-admin/PlanUpgradeRequests";
import useSWR from "swr";

interface SuperAdminStats {
  total_companies: number;
  total_admins: number;
  total_agents: number;
  total_plans: number;
  active_sessions: number;
  pending_sessions: number;
  total_users: number;
  monthly_revenue: number;
}

export default function Dashboard() {
  const { data: stats, isLoading } = useSWR<SuperAdminStats>(
    "/auth/super-admin-stats/"
  );

  if (isLoading) {
    return (
      <div className="pt-4 space-y-5">
        <h2 className="font-bold text-2xl">Dashboard</h2>
        <div className="grid grid-cols-2 md:grid-cols-2 xl:grid-cols-4 gap-10">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
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
      <h2 className="font-bold text-2xl">Super Admin Dashboard</h2>
      <div className="grid grid-cols-2 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <Card title="Total Companies" count={stats?.total_companies || 0} />
        <Card title="Total Admins" count={stats?.total_admins || 0} />
        <Card title="Total Agents" count={stats?.total_agents || 0} />
        <Card title="Active Plans" count={stats?.total_plans || 0} />
        <Card title="Active Sessions" count={stats?.active_sessions || 0} />
        <Card title="Pending Sessions" count={stats?.pending_sessions || 0} />
        <Card title="Total Users" count={stats?.total_users || 0} />
        <Card title="Monthly Revenue" count={stats?.monthly_revenue || 0} />
      </div>

      {/* Plan Upgrade Requests Section */}
      <div className="mt-8">
        <PlanUpgradeRequests />
      </div>
    </div>
  );
}
