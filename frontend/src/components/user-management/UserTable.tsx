import React from "react";
import type { ColumnsType } from "antd/es/table";
import AppTable from "../../share/form/AppTable";
import { Button, message, Popconfirm, Tooltip } from "antd";
import { FiPlus } from "react-icons/fi";
import { CSVLink } from "react-csv";
import { CiExport } from "react-icons/ci";
import { useState } from "react";
import type { TableRowSelection } from "antd/es/table/interface";
import { FaHeart, FaRegHeart } from "react-icons/fa6";
import { MdClear } from "react-icons/md";
import useSWR from "swr";
import { axiosClient } from "../../config/axiosConfig";
import { useSearchParams } from "react-router-dom";

interface UserTableProps {
  handleOpenModal: () => void;
}

interface UserProfile {
  id: number;
  session_id: string;
  persistent_user_id: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
  country_code: string;
  is_favorite: boolean;
  created_at: string;
  last_used: string;
}

interface DataType extends UserProfile {
  key: React.Key;
  sn: number;
}

export default function UserTable({ handleOpenModal }: UserTableProps) {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [searchParams, setSearchParams] = useSearchParams({});
  const page = Number(searchParams.get("page")) || 1;

  // Fetch user profiles
  const { data, isLoading, mutate } = useSWR(
    `/admin-dashboard/user-profiles/?page=${page}`
  );

  const handleToggleFavorite = async (
    profileId: number,
    currentFavorite: boolean
  ) => {
    try {
      await axiosClient.post(
        "/admin-dashboard/user-profiles/toggle-favorite/",
        {
          profile_id: profileId,
        }
      );
      message.success(
        `User ${currentFavorite ? "removed from" : "added to"} favorites`
      );
      mutate(); // Refresh data
    } catch (error: any) {
      message.error(
        error?.response?.data?.error || "Failed to update favorite status"
      );
    }
  };

  const handleClearNonFavorites = async () => {
    try {
      const response = await axiosClient.post(
        "/admin-dashboard/user-profiles/clear-non-favorites/"
      );
      message.success(response.data.message);
      mutate(); // Refresh data
    } catch (error: any) {
      message.error(error?.response?.data?.error || "Failed to clear profiles");
    }
  };

  const handlePagination = (pagination: number) => {
    setSearchParams({
      page: pagination.toString(),
    });
  };

  const onSelectChange = (newSelectedRowKeys: React.Key[]) => {
    console.log("selectedRowKeys changed: ", newSelectedRowKeys);
    setSelectedRowKeys(newSelectedRowKeys);
  };

  const rowSelection: TableRowSelection<DataType> = {
    selectedRowKeys,
    onChange: onSelectChange,
  };
  const columns: ColumnsType<DataType> = [
    {
      title: "SN",
      dataIndex: "sn",
      width: 60,
      render: (value) => <span className="font-medium">{value}</span>,
    },
    {
      title: "Name",
      dataIndex: "name",
      render: (value) => (
        <span className="font-medium text-gray-900">{value}</span>
      ),
    },
    {
      title: "Phone",
      dataIndex: "phone",
      render: (value, record) => (
        <span className="text-gray-600">
          {record.country_code} {value}
        </span>
      ),
    },
    {
      title: "Email Address",
      dataIndex: "email",
      render: (value) => <span className="text-gray-600">{value || "—"}</span>,
    },
    {
      title: "Address",
      dataIndex: "address",
      render: (value) => <span className="text-gray-600">{value || "—"}</span>,
    },
    {
      title: "Last Used",
      dataIndex: "last_used",
      render: (value) => (
        <span className="text-gray-500 text-sm">
          {value ? new Date(value).toLocaleString() : "—"}
        </span>
      ),
    },
    {
      title: "Favorite",
      dataIndex: "is_favorite",
      width: 80,
      align: "center",
      render: (_, record) => (
        <Tooltip
          title={
            record.is_favorite ? "Remove from favorites" : "Add to favorites"
          }
        >
          <div
            className="cursor-pointer hover:scale-110 transition-transform"
            onClick={() => handleToggleFavorite(record.id, record.is_favorite)}
          >
            {record.is_favorite ? (
              <FaHeart size={18} className="text-red-500" />
            ) : (
              <FaRegHeart
                size={18}
                className="text-gray-400 hover:text-red-500"
              />
            )}
          </div>
        </Tooltip>
      ),
    },
  ];

  const csvHeaders = [
    { label: "SN", key: "sn" },
    { label: "Name", key: "name" },
    { label: "Phone", key: "phone" },
    { label: "Email", key: "email" },
    { label: "Address", key: "address" },
    { label: "Country Code", key: "country_code" },
    { label: "Is Favorite", key: "is_favorite" },
    { label: "Created At", key: "created_at" },
    { label: "Last Used", key: "last_used" },
  ];

  // Prepare table data
  const tableData: DataType[] =
    data?.results?.map((profile: UserProfile, index: number) => ({
      ...profile,
      key: profile.id,
      sn: (page - 1) * 10 + index + 1, // Assuming 10 items per page
    })) || [];

  const totalCount = data?.count || 0;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="flex gap-3 items-center">
          <h6 className="font-bold text-xl">User Profiles ({totalCount})</h6>
          <CSVLink
            data={tableData.filter((item) =>
              selectedRowKeys.includes(item.key)
            )}
            headers={csvHeaders}
            filename={`user-profiles-${
              new Date().toISOString().split("T")[0]
            }.csv`}
          >
            <Button
              type="primary"
              icon={<CiExport size={16} />}
              disabled={selectedRowKeys.length === 0}
            >
              Export ({selectedRowKeys.length})
            </Button>
          </CSVLink>
          <Popconfirm
            title="Clear Non-Favorite Users"
            description="This will delete all users except those marked as favorites. Are you sure?"
            onConfirm={handleClearNonFavorites}
            okText="Yes, Clear"
            cancelText="Cancel"
          >
            <Button type="primary" danger icon={<MdClear size={16} />}>
              Clear Non-Favorites
            </Button>
          </Popconfirm>
        </div>
        <Button
          type="primary"
          className="!bg-yellow"
          icon={<FiPlus size={15} />}
          onClick={handleOpenModal}
        >
          Add User
        </Button>
      </div>

      <AppTable
        rowKey="id"
        rowSelection={rowSelection as any}
        columns={columns as any}
        dataSource={tableData as any}
        loading={isLoading}
        total={totalCount}
        paginationData={page}
        handlePagination={handlePagination}
      />
    </div>
  );
}
