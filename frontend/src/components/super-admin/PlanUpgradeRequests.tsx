import React, { useState } from "react";
import {
  Card,
  Table,
  Button,
  Modal,
  message,
  Tag,
  Space,
  Typography,
} from "antd";
import {
  CheckOutlined,
  CloseOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";
import useSWR from "swr";
import { axiosClient } from "../../config/axiosConfig";

const { Title, Text } = Typography;

interface RequestedBy {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

interface PlanUpgradeRequest {
  id: number;
  company_id: string;
  company_name: string;
  current_plan: string;
  requested_plan: string;
  reason: string;
  status: "PENDING" | "APPROVED" | "DECLINED";
  requested_at: string;
  requested_by: RequestedBy;
  reviewed_by?: RequestedBy;
  reviewed_at?: string;
  review_notes?: string;
}

const PlanUpgradeRequests: React.FC = () => {
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [selectedRequest, setSelectedRequest] =
    useState<PlanUpgradeRequest | null>(null);
  const [reviewAction, setReviewAction] = useState<"approve" | "decline">(
    "approve"
  );
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const {
    data: response,
    error,
    mutate,
    isLoading,
  } = useSWR("/admin-dashboard/plan-upgrade-requests/", () =>
    axiosClient.get("/admin-dashboard/plan-upgrade-requests/").then((res) => res.data)
  );

  // Extract requests from response - the API returns an object with requests array
  const requests = Array.isArray(response) ? response : response?.requests || [];

  const handleReviewRequest = (
    request: PlanUpgradeRequest,
    action: "approve" | "decline"
  ) => {
    setSelectedRequest(request);
    setReviewAction(action);
    setReviewModalVisible(true);
  };

  const submitReviewRequest = async () => {
    if (!selectedRequest) return;

    setLoading(true);
    try {
      await axiosClient.post(`/admin-dashboard/plan-upgrade-requests/${selectedRequest.id}/review/`, {
        action: reviewAction,
        notes: `${reviewAction === "approve" ? "Approved" : "Declined"} by SuperAdmin`
      });

      message.success(
        `Plan upgrade request ${
          reviewAction === "approve" ? "approved" : "declined"
        } successfully!`
      );

      // Refresh the data
      mutate();
      setReviewModalVisible(false);
      setSelectedRequest(null);
    } catch (error: any) {
      console.error("Review error:", error);
      message.error(error.response?.data?.error || "Failed to process review. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return <Tag color="orange">Pending</Tag>;
      case "approved":
        return <Tag color="green">Approved</Tag>;
      case "rejected":
      case "declined":
        return <Tag color="red">Declined</Tag>;
      default:
        return <Tag color="default">{status}</Tag>;
    }
  };

  const getPlanTag = (plan: string) => {
    const colors: { [key: string]: string } = {
      Bronze: "orange",
      Silver: "gray",
      Gold: "gold",
      Platinum: "blue",
      Diamond: "purple",
      Custom: "green",
    };
    return <Tag color={colors[plan] || "default"}>{plan}</Tag>;
  };

  const columns = [
    {
      title: "S.N",
      key: "serialNumber",
      width: 50,
      align: "center" as const,
      render: (_: unknown, __: PlanUpgradeRequest, index: number) => (
        <span className="text-gray-600 font-medium">
          {(currentPage - 1) * pageSize + index + 1}
        </span>
      ),
    },
    {
      title: "Company Name",
      dataIndex: "company_name",
      key: "company_name",
      width: 150,
      render: (text: string) => (
        <div className="font-semibold text-gray-800">{text}</div>
      ),
    },
    {
      title: "Company ID",
      dataIndex: "company_id",
      key: "company_id",
      width: 120,
      render: (company_id: string) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {company_id}
        </span>
      ),
    },
    {
      title: "Current Plan",
      dataIndex: "current_plan",
      key: "current_plan",
      width: 120,
      align: "center" as const,
      render: (plan: string) => getPlanTag(plan),
    },
    {
      title: "Requested Plan",
      dataIndex: "requested_plan",
      key: "requested_plan",
      width: 120,
      align: "center" as const,
      render: (plan: string) => getPlanTag(plan),
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 100,
      align: "center" as const,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: "Requested Date",
      dataIndex: "requested_at",
      key: "requested_at",
      width: 120,
      align: "center" as const,
      render: (date: string) => (
        <span className="text-gray-600">
          {new Date(date).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
          })}
        </span>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      width: 160,
      align: "center" as const,
      render: (_: unknown, record: PlanUpgradeRequest) => {
        if (record.status.toLowerCase() !== "pending") {
          return (
            <span className="text-gray-500 italic">
              {record.status.toLowerCase() === "approved" ? "Approved" : "Declined"}
            </span>
          );
        }

        return (
          <Space size="small">
            <Button
              type="primary"
              size="small"
              icon={<CheckOutlined />}
              onClick={() => handleReviewRequest(record, "approve")}
              className="bg-green-600 border-green-600 hover:bg-green-700 hover:border-green-700"
            >
              Approve
            </Button>
            <Button
              danger
              size="small"
              icon={<CloseOutlined />}
              onClick={() => handleReviewRequest(record, "decline")}
            >
              Decline
            </Button>
          </Space>
        );
      },
    },
  ];

  if (error) {
    return (
      <Card>
        <div className="text-center py-8">
          <ExclamationCircleOutlined className="text-4xl text-red-500 mb-4" />
          <Title level={4}>Failed to load upgrade requests</Title>
          <Text type="secondary">Please try refreshing the page</Text>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card
        title={
          <div className="flex justify-between items-center">
            <Title level={4} style={{ margin: 0 }}>
              Plan Upgrade Requests
            </Title>
            <Tag color="blue">
              {Array.isArray(requests)
                ? requests.filter(
                    (r: PlanUpgradeRequest) => r.status.toLowerCase() === "pending"
                  ).length
                : 0}{" "}
              Pending
            </Tag>
          </div>
        }
        className="shadow-sm"
      >
        <Table
          columns={columns}
          dataSource={requests || []}
          loading={isLoading}
          rowKey="id"
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} requests`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size || 10);
            },
          }}
        />
      </Card>

      {/* Review Modal */}
      <Modal
        title={
          <div className="flex items-center space-x-2">
            {reviewAction === "approve" ? (
              <CheckOutlined className="text-green-600" />
            ) : (
              <CloseOutlined className="text-red-600" />
            )}
            <span>
              {reviewAction === "approve" ? "Approve" : "Decline"} Plan Upgrade
              Request
            </span>
          </div>
        }
        open={reviewModalVisible}
        onOk={submitReviewRequest}
        onCancel={() => {
          setReviewModalVisible(false);
          setSelectedRequest(null);
        }}
        confirmLoading={loading}
        okText={reviewAction === "approve" ? "Approve" : "Decline"}
        okButtonProps={{
          danger: reviewAction === "decline",
          className:
            reviewAction === "approve"
              ? "bg-green-600 border-green-600 hover:bg-green-700"
              : "",
        }}
      >
        {selectedRequest && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Text strong className="text-gray-700">
                    Company Name:
                  </Text>
                  <div className="font-medium">
                    {selectedRequest.company_name}
                  </div>
                </div>
                <div>
                  <Text strong className="text-gray-700">
                    Company ID:
                  </Text>
                  <div className="font-medium text-blue-600">
                    {selectedRequest.company_id}
                  </div>
                </div>
                <div>
                  <Text strong className="text-gray-700">
                    Current Plan:
                  </Text>
                  <div className="mt-1">
                    {getPlanTag(selectedRequest.current_plan)}
                  </div>
                </div>
                <div>
                  <Text strong className="text-gray-700">
                    Requested Plan:
                  </Text>
                  <div className="mt-1">
                    {getPlanTag(selectedRequest.requested_plan)}
                  </div>
                </div>
              </div>
            </div>

            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <Text className="text-gray-600">
                Are you sure you want to{" "}
                <strong
                  className={
                    reviewAction === "approve"
                      ? "text-green-600"
                      : "text-red-600"
                  }
                >
                  {reviewAction}
                </strong>{" "}
                this plan upgrade request?
              </Text>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

export default PlanUpgradeRequests;
