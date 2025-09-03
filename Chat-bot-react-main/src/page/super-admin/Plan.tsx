import { useState } from "react";

import {
  Button,
  Input,
  Select,
  DatePicker,
  Modal,
  Table,
  Dropdown,
  type MenuProps,
} from "antd";
import { FiSearch, FiEye, FiXCircle, FiMoreVertical } from "react-icons/fi";
import useSWR from "swr";

const { RangePicker } = DatePicker;

// Types
interface PlanHistory {
  plan_name: string;
  start_date: string;
  end_date: string;
  price: number;
}

interface CompanySubscription {
  id: number;
  company_name: string;
  company_id: string;
  plan_name: string;
  price: number;
  status: string;
  created_at: string;
  expiry_date: string;
  plan_history?: PlanHistory[];
}

// Plan cards data
const planCards = [
  {
    id: 1,
    name: "Bronze",
    price: 2000,
    maxAgent: 2,
    bgColor: "bg-gradient-to-br from-amber-100 to-orange-200",
    borderColor: "border-amber-300",
    textColor: "text-amber-800",
    theme: "bronze",
  },
  {
    id: 2,
    name: "Silver",
    price: 4000,
    maxAgent: 4,
    bgColor: "bg-gradient-to-br from-gray-100 to-slate-200",
    borderColor: "border-gray-300",
    textColor: "text-gray-800",
    theme: "silver",
  },
  {
    id: 3,
    name: "Gold",
    price: 6000,
    maxAgent: 6,
    bgColor: "bg-gradient-to-br from-yellow-100 to-amber-200",
    borderColor: "border-yellow-400",
    textColor: "text-yellow-800",
    theme: "gold",
  },
  {
    id: 4,
    name: "Platinum",
    price: 8000,
    maxAgent: 8,
    bgColor: "bg-gradient-to-br from-blue-100 to-indigo-200",
    borderColor: "border-blue-300",
    textColor: "text-blue-800",
    theme: "platinum",
  },
  {
    id: 5,
    name: "Diamond",
    price: 10000,
    maxAgent: 10,
    bgColor: "bg-gradient-to-br from-cyan-100 to-blue-200",
    borderColor: "border-cyan-300",
    textColor: "text-cyan-800",
    theme: "diamond",
  },
];

export default function Plan() {
  const [loading, setLoading] = useState<boolean>(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [selectedCompany, setSelectedCompany] =
    useState<CompanySubscription | null>(null);

  // Pagination state for reports
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Filter states for reports
  const [searchText, setSearchText] = useState("");
  const [selectedPlan, setSelectedPlan] = useState("");
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);

  // Build query string with filters for company reports
  const buildQueryString = () => {
    const params = new URLSearchParams();
    params.set("page", page.toString());
    params.set("page_size", pageSize.toString());

    if (searchText) params.set("search", searchText);
    if (selectedPlan) params.set("plan_name", selectedPlan);
    if (dateRange) {
      params.set("created_from", dateRange[0]);
      params.set("created_to", dateRange[1]);
    }

    return params.toString();
  };

  // Fetch company subscription data for reports
  const {
    data: reportData,
    isLoading: reportLoading,
    mutate,
  } = useSWR(`/auth/company-subscriptions/?${buildQueryString()}`);

  // Assume API returns { results: [], count: number }
  const companies = reportData?.results || [];
  const total = reportData?.count || 0;

  const planFilterOptions = [
    { label: "All Plans", value: "" },
    { label: "Bronze", value: "bronze" },
    { label: "Silver", value: "silver" },
    { label: "Gold", value: "gold" },
    { label: "Platinum", value: "platinum" },
    { label: "Diamond", value: "diamond" },
    { label: "Custom", value: "custom" },
  ];

  // Handle cancel subscription
  const handleCancelSubscription = async (assignmentId: number) => {
    try {
      setLoading(true);
      // Get token from localStorage or context
      const token = localStorage.getItem("access_token");

      // API call to cancel subscription using assignment ID
      const response = await fetch(
        `http://localhost:8001/api/auth/cancel-subscription-by-assignment/${assignmentId}/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            reason: "Subscription cancelled by admin",
          }),
        }
      );

      if (response.ok) {
        mutate(); // Refresh the data
        setViewModalVisible(false);
      } else {
        console.error("Failed to cancel subscription:", response.statusText);
      }
    } catch (error) {
      console.error("Error canceling subscription:", error);
    } finally {
      setLoading(false);
    }
  };

  // Report table columns
  const reportColumns = [
    {
      title: "S.N",
      key: "serialNumber",
      render: (_: unknown, __: unknown, index: number) =>
        (page - 1) * pageSize + index + 1,
      width: 60,
    },
    {
      title: "Company Name",
      dataIndex: "company_name",
      key: "company_name",
    },
    {
      title: "Company ID",
      dataIndex: "company_id",
      key: "company_id",
    },
    {
      title: "Plan",
      dataIndex: "plan_name",
      key: "plan_name",
      render: (planName: string) => (
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            planName === "Bronze"
              ? "bg-amber-100 text-amber-800"
              : planName === "Silver"
              ? "bg-gray-100 text-gray-800"
              : planName === "Gold"
              ? "bg-yellow-100 text-yellow-800"
              : planName === "Platinum"
              ? "bg-blue-100 text-blue-800"
              : planName === "Diamond"
              ? "bg-cyan-100 text-cyan-800"
              : "bg-purple-100 text-purple-800"
          }`}
        >
          {planName}
        </span>
      ),
    },
    {
      title: "Price",
      dataIndex: "price",
      key: "price",
      render: (price: number) => `NPR ${price?.toLocaleString()}`,
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            status === "active"
              ? "bg-green-100 text-green-800"
              : status === "pending"
              ? "bg-yellow-100 text-yellow-800"
              : status === "cancelled" || status === "expired"
              ? "bg-red-100 text-red-800"
              : "bg-gray-100 text-gray-800"
          }`}
        >
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      ),
    },
    {
      title: "Action",
      key: "action",
      render: (record: CompanySubscription) => {
        const menuItems: MenuProps["items"] = [
          {
            key: "view",
            label: "View Details",
            icon: <FiEye />,
            onClick: () => {
              setSelectedCompany(record);
              setViewModalVisible(true);
            },
          },
          ...(record.status === "active"
            ? [
                {
                  key: "cancel",
                  label: "Cancel Subscription",
                  icon: <FiXCircle />,
                  danger: true,
                  onClick: () => handleCancelSubscription(record.id),
                },
              ]
            : []),
        ];

        return (
          <Dropdown
            menu={{ items: menuItems }}
            trigger={["click"]}
            placement="bottomRight"
          >
            <Button
              type="text"
              size="small"
              icon={<FiMoreVertical />}
              className="flex items-center justify-center"
            />
          </Dropdown>
        );
      },
    },
  ];

  return (
    <div className="pt-4 space-y-6">
      <h2 className="font-bold text-2xl">Plans</h2>

      {/* Filters Section */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium mb-1">Search</label>
            <Input
              placeholder="Search by company name..."
              prefix={<FiSearch />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Plan Type</label>
            <Select
              style={{ width: "100%" }}
              placeholder="Select plan type"
              options={planFilterOptions}
              value={selectedPlan}
              onChange={setSelectedPlan}
              allowClear
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Date Range</label>
            <RangePicker
              style={{ width: "100%" }}
              onChange={(dates) => {
                if (dates) {
                  setDateRange([
                    dates[0]?.format("YYYY-MM-DD") || "",
                    dates[1]?.format("YYYY-MM-DD") || "",
                  ]);
                } else {
                  setDateRange(null);
                }
              }}
            />
          </div>
          <div>
            <Button
              type="primary"
              onClick={() => {
                setPage(1); // Reset to first page when filtering
                mutate(); // Trigger refetch
              }}
            >
              Apply Filters
            </Button>
          </div>
        </div>
      </div>

      {/* Plan Cards Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Available Plans</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {planCards.map((plan) => (
            <div
              key={plan.id}
              className={`${plan.bgColor} ${plan.borderColor} ${plan.textColor} border-2 rounded-lg p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1`}
            >
              <div className="text-center space-y-3">
                <h4 className="text-xl font-bold">{plan.name}</h4>
                <div className="text-3xl font-bold">
                  NPR {plan.price.toLocaleString()}
                </div>
                <div className="text-sm opacity-75">/Mo</div>
                <div className="text-sm opacity-80">
                  Max {plan.maxAgent} Agents
                </div>
                <div
                  className={`inline-block px-3 py-1 rounded-full text-xs font-medium bg-white bg-opacity-50`}
                >
                  {plan.theme.toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Reports Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Company Subscription Reports</h3>
        <div className="bg-white rounded-lg shadow-sm border">
          <Table
            dataSource={companies}
            columns={reportColumns}
            loading={reportLoading}
            pagination={{
              total,
              current: page,
              pageSize,
              showSizeChanger: false,
              onChange: setPage,
            }}
            rowKey="id"
            scroll={{ x: "max-content" }}
          />
        </div>
      </div>

      {/* Company Details Modal */}
      <Modal
        title={`${selectedCompany?.company_name} - Subscription Details`}
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            Close
          </Button>,
          <Button
            key="cancel"
            type="primary"
            danger
            icon={<FiXCircle />}
            loading={loading}
            onClick={() => handleCancelSubscription(selectedCompany?.id || 0)}
          >
            Cancel Subscription
          </Button>,
        ]}
        width={600}
      >
        {selectedCompany && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500">
                  Plan Created Date
                </label>
                <p className="text-base">
                  {new Date(selectedCompany.created_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">
                  Expiry Date
                </label>
                <p className="text-base">
                  {new Date(selectedCompany.expiry_date).toLocaleDateString()}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">
                  Current Plan
                </label>
                <p className="text-base font-semibold">
                  {selectedCompany.plan_name}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">
                  Price
                </label>
                <p className="text-base font-semibold">
                  NPR {selectedCompany.price?.toLocaleString()}
                </p>
              </div>
            </div>

            {selectedCompany.plan_history &&
              selectedCompany.plan_history.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-2">
                    Plan History
                  </label>
                  <div className="space-y-2">
                    {selectedCompany.plan_history.map(
                      (history: PlanHistory, index: number) => (
                        <div key={index} className="bg-gray-50 p-3 rounded-md">
                          <div className="flex justify-between items-center">
                            <span className="font-medium">
                              {history.plan_name}
                            </span>
                            <span className="text-sm text-gray-500">
                              {new Date(
                                history.start_date
                              ).toLocaleDateString()}{" "}
                              -{" "}
                              {new Date(history.end_date).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600">
                            Price: NPR {history.price?.toLocaleString()}
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}
          </div>
        )}
      </Modal>
    </div>
  );
}
