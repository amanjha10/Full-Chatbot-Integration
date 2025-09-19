import { useState } from "react";
import Card from "../components/dashboard/Card";
import UserTable from "../components/user-management/UserTable";
import AddUserModal from "../components/user-management/AddUserModal";
import useSWR from "swr";

interface UserManagementStats {
  total_users: number;
  favorite_users: number;
  active_users: number;
  new_users_today: number;
}

export default function UserManagement() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: stats, isLoading } = useSWR<UserManagementStats>(
    "/admin-dashboard/user-profiles/stats/"
  );

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  if (isLoading) {
    return (
      <div className="pt-4 space-y-5">
        <h2 className="font-bold text-2xl">User Management</h2>
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
      <h2 className="font-bold text-2xl">User Management</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6">
        <Card title="Total Users" count={stats?.total_users || 0} />
        <Card title="Favorite Users" count={stats?.favorite_users || 0} />
        <Card title="Active Users" count={stats?.active_users || 0} />
        <Card title="New Today" count={stats?.new_users_today || 0} />
      </div>
      <UserTable handleOpenModal={handleOpenModal} />
      {isModalOpen && (
        <AddUserModal isModalOpen={isModalOpen} onCancel={handleCloseModal} />
      )}
    </div>
  );
}
