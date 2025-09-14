import { useState } from "react";

import {
  Button,
  Input,
  Select,
  DatePicker,
  Modal,
  Table,
  Dropdown,
  Card,
  Form,
  InputNumber,
  message,
  Tag,
  Pagination,
  type MenuProps,
} from "antd";
import { FiSearch, FiEye, FiXCircle, FiMoreVertical, FiEdit2, FiSave, FiX } from "react-icons/fi";
import useSWR from "swr";
import { axiosClient } from "../../config/axiosConfig";

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
  max_agents: string;
  status: string;
  created_at: string;
  expiry_date: string | null;
  plan_history?: PlanHistory[];
}

interface PlanData {
  id: number;
  name: string;
  for_whom: string;
  price: number | null;
  max_agents: string;
  features_line: string;
  css_meta: {
    gradient: string;
    text_color: string;
    border_color: string;
    button_color: string;
    shine_color: string;
  };
  icon: string;
  sort_order: number;
}

// Plan card editing state
interface EditingPlan {
  id: number;
  name: string;
  for_whom: string;
  price: number | null;
  max_agents: string;
  features_line: string;
}



// Helper functions to convert Tailwind classes to CSS
const getGradientStyle = (gradient?: string) => {
  if (!gradient) return 'linear-gradient(135deg, #f3f4f6, #e5e7eb)';

  const gradientMap: { [key: string]: string } = {
    'from-amber-800 via-yellow-600 to-amber-900': 'linear-gradient(135deg, #92400e, #ca8a04, #78350f)',
    'from-gray-600 via-gray-400 to-gray-700': 'linear-gradient(135deg, #4b5563, #9ca3af, #374151)',
    'from-yellow-600 via-yellow-400 to-yellow-700': 'linear-gradient(135deg, #ca8a04, #facc15, #a16207)',
    'from-purple-800 via-purple-600 to-purple-900': 'linear-gradient(135deg, #6b21a8, #9333ea, #581c87)',
    'from-cyan-600 via-blue-500 to-cyan-700': 'linear-gradient(135deg, #0891b2, #3b82f6, #0e7490)',
    'from-indigo-800 via-indigo-600 to-indigo-900': 'linear-gradient(135deg, #3730a3, #4f46e5, #312e81)',
  };

  return gradientMap[gradient] || 'linear-gradient(135deg, #f3f4f6, #e5e7eb)';
};

const getBorderColor = (borderColor?: string) => {
  if (!borderColor) return '#d1d5db';

  const colorMap: { [key: string]: string } = {
    'border-amber-400': '#fbbf24',
    'border-gray-300': '#d1d5db',
    'border-yellow-300': '#fde047',
    'border-purple-400': '#c084fc',
    'border-cyan-300': '#67e8f9',
    'border-indigo-400': '#818cf8',
  };

  return colorMap[borderColor] || '#d1d5db';
};

export default function Plan() {
  const [loading, setLoading] = useState<boolean>(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [selectedCompany, setSelectedCompany] =
    useState<CompanySubscription | null>(null);

  // Plan editing states
  const [editingPlan, setEditingPlan] = useState<number | null>(null);
  const [editForm] = Form.useForm();

  // Plan change modal states
  const [changePlanModalVisible, setChangePlanModalVisible] = useState(false);
  const [selectedCompanyForChange, setSelectedCompanyForChange] = useState<CompanySubscription | null>(null);
  const [changePlanForm] = Form.useForm();
  const [changingPlan, setChangingPlan] = useState(false);
  const [selectedPlanForChange, setSelectedPlanForChange] = useState<string>('');



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

  // Fetch plans data from SuperAdmin endpoint
  const {
    data: plansData,
    isLoading: plansLoading,
    mutate: mutatePlans,
  } = useSWR("/chatbot/superadmin/plans/");



  // Fetch company subscription data for reports
  const {
    data: reportData,
    isLoading: reportLoading,
    mutate,
  } = useSWR(`/auth/company-subscriptions/?${buildQueryString()}`);

  // Assume API returns { results: [], count: number }
  const companies = reportData?.results || [];
  const total = reportData?.count || 0;
  const plans: PlanData[] = plansData || [];

  const planFilterOptions = [
    { label: "All Plans", value: "" },
    { label: "Bronze", value: "bronze" },
    { label: "Silver", value: "silver" },
    { label: "Gold", value: "gold" },
    { label: "Platinum", value: "platinum" },
    { label: "Diamond", value: "diamond" },
    { label: "Custom", value: "custom" },
  ];

  // Plan editing functions
  const handleEditPlan = (plan: PlanData) => {
    setEditingPlan(plan.id);
    editForm.setFieldsValue({
      name: plan.name,
      for_whom: plan.for_whom,
      price: plan.price,
      max_agents: plan.max_agents,
      features_line: plan.features_line,
    });
  };

  const handleSavePlan = async () => {
    try {
      const values = await editForm.validateFields();
      await axiosClient.put(`/chatbot/superadmin/plans/${editingPlan}/`, values);
      message.success("Plan updated successfully!");
      setEditingPlan(null);
      mutatePlans();
    } catch (error) {
      message.error("Failed to update plan");
    }
  };

  const handleCancelEdit = () => {
    setEditingPlan(null);
    editForm.resetFields();
  };



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

  // Handle plan change
  const handleChangePlan = (company: CompanySubscription) => {
    setSelectedCompanyForChange(company);
    setChangePlanModalVisible(true);
    changePlanForm.resetFields();
    setSelectedPlanForChange('');
  };

  const handlePlanChangeSubmit = async () => {
    try {
      setChangingPlan(true);
      const values = await changePlanForm.validateFields();

      const requestData: any = {
        plan_id: values.plan_id,
        reason: values.reason || 'Manual plan change by SuperAdmin'
      };

      // Add custom fields if Custom plan is selected
      if (selectedPlanForChange === 'Custom') {
        requestData.custom_max_agents = values.custom_max_agents;
        requestData.custom_price = values.custom_price;
      }

      await axiosClient.post(
        `/chatbot/superadmin/company/${selectedCompanyForChange?.company_id}/change-plan/`,
        requestData
      );

      message.success("Plan changed successfully!");
      setChangePlanModalVisible(false);
      mutate(); // Refresh the data
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || "Failed to change plan";
      message.error(errorMessage);
    } finally {
      setChangingPlan(false);
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
      title: "Max Agents",
      dataIndex: "max_agents",
      key: "max_agents",
      render: (maxAgents: string) => maxAgents || "N/A",
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
          {
            key: "change",
            label: "Change Plan",
            icon: <FiEdit2 />,
            onClick: () => handleChangePlan(record),
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
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-3 gap-4 max-w-6xl mx-auto">
          {plansLoading ? (
            <div className="col-span-full text-center py-8">Loading plans...</div>
          ) : plansData && plansData.length > 0 ? (
            plansData.map((plan) => (
              <Card
                key={plan.id}
                className="relative overflow-hidden border-2 hover:shadow-xl transition-all duration-300"
                style={{
                  background: getGradientStyle(plan.css_meta?.gradient),
                  borderColor: getBorderColor(plan.css_meta?.border_color),
                  color: plan.css_meta?.text_color === 'text-white' ? 'white' : 'black'
                }}
              >
                <div className="absolute top-2 right-2">
                  {editingPlan === plan.id ? (
                    <div className="flex gap-1">
                      <Button
                        type="text"
                        size="small"
                        icon={<FiSave />}
                        onClick={handleSavePlan}
                        className="text-white hover:bg-white hover:bg-opacity-20"
                      />
                      <Button
                        type="text"
                        size="small"
                        icon={<FiX />}
                        onClick={handleCancelEdit}
                        className="text-white hover:bg-white hover:bg-opacity-20"
                      />
                    </div>
                  ) : (
                    <Button
                      type="text"
                      size="small"
                      icon={<FiEdit2 />}
                      onClick={() => handleEditPlan(plan)}
                      className="text-white hover:bg-white hover:bg-opacity-20"
                    />
                  )}
                </div>

                <div className="text-center space-y-2 p-4">
                  <div className="text-3xl mb-2" style={{ fontSize: '2.5rem' }}>
                    {plan.icon || '📦'}
                  </div>

                  {editingPlan === plan.id ? (
                    <Form form={editForm} layout="vertical">
                      <Form.Item name="name" className="mb-1">
                        <Input className="text-center font-bold text-base" placeholder="Plan Name" />
                      </Form.Item>
                      <Form.Item name="for_whom" className="mb-1">
                        <Input className="text-center text-xs" placeholder="For whom" />
                      </Form.Item>
                      <Form.Item name="price" className="mb-1">
                        <InputNumber
                          className="w-full text-center"
                          size="small"
                          formatter={(value) => value ? `₨ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',') : ''}
                          parser={(value) => value!.replace(/₨\s?|(,*)/g, '')}
                          placeholder="Price (leave empty for custom)"
                        />
                      </Form.Item>
                      <Form.Item name="max_agents" className="mb-2">
                        <Input className="text-center" placeholder="Max Agents" />
                      </Form.Item>
                      <Form.Item name="features_line" className="mb-2">
                        <Input className="text-center text-xs" placeholder="Features (one line)" />
                      </Form.Item>
                    </Form>
                  ) : (
                    <div className="space-y-2">
                      <h4 className="text-xl font-bold">{plan.name || 'Plan Name'}</h4>
                      <p className="text-sm opacity-80">{plan.for_whom || 'For everyone'}</p>
                      <div className="text-2xl font-bold">
                        {plan.price ? `₨${plan.price.toLocaleString()}` : "Custom"}
                      </div>
                      <div className="text-sm opacity-75">/month</div>
                      <div className="text-sm opacity-80">
                        Max {plan.max_agents || 'Unlimited'} Agents
                      </div>
                      <div className="text-sm opacity-70 mt-2">
                        {plan.features_line || 'AI-powered Chatbot'}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            ))
          ) : (
            <div className="col-span-full text-center py-8 text-gray-500">
              <p>No plans available</p>
              <p className="text-sm mt-2">
                Plans data: {plansData ? `${plansData.length} plans found` : 'No data'}
              </p>
            </div>
          )}
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

      {/* Plan Change Modal */}
      <Modal
        title={`Change Plan for ${selectedCompanyForChange?.company_name}`}
        open={changePlanModalVisible}
        onCancel={() => setChangePlanModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setChangePlanModalVisible(false)}>
            Cancel
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={changingPlan}
            onClick={handlePlanChangeSubmit}
          >
            Change Plan
          </Button>,
        ]}
        width={600}
      >
        <Form form={changePlanForm} layout="vertical">
          <Form.Item
            name="plan_id"
            label="Select New Plan"
            rules={[{ required: true, message: 'Please select a plan' }]}
          >
            <Select
              placeholder="Choose a plan"
              onChange={(value, option: any) => setSelectedPlanForChange(option?.label || '')}
            >
              {plans.map((plan) => (
                <Select.Option key={plan.id} value={plan.id} label={plan.name}>
                  {plan.name} - ₨{plan.price ? plan.price.toLocaleString() : 'Custom'} ({plan.max_agents} agents)
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          {selectedPlanForChange === 'Custom' && (
            <>
              <Form.Item
                name="custom_max_agents"
                label="Max Agents"
                rules={[{ required: true, message: 'Please enter max agents' }]}
              >
                <InputNumber min={1} placeholder="Enter max agents" style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item
                name="custom_price"
                label="Price (₨)"
                rules={[{ required: true, message: 'Please enter price' }]}
              >
                <InputNumber min={0} placeholder="Enter price" style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}

          <Form.Item
            name="reason"
            label="Reason for Change"
          >
            <Input.TextArea
              rows={3}
              placeholder="Enter reason for plan change (optional)"
            />
          </Form.Item>

          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
            <p className="text-sm text-yellow-800">
              <strong>Note:</strong> Changing the plan will immediately affect the company's agent limits and features.
              Make sure to consider the current agent usage before downgrading.
            </p>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
